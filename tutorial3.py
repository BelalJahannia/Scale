import math
import numpy as np
import matplotlib.pyplot as plt

from scalesim.compute.operand_matrix import operand_matrix as opmat
from scalesim.topology_utils import topologies
from scalesim.scale_config import scale_config

from scalesim.compute.systolic_compute_os import systolic_compute_os
from scalesim.compute.systolic_compute_ws import systolic_compute_ws
from scalesim.compute.systolic_compute_is import systolic_compute_is
from scalesim.memory.double_buffered_scratchpad_mem import double_buffered_scratchpad as mem_dbsp


class scaled_out_simulator:
    def __init__(self):
        self.topo_obj = topologies()
        self.single_arr_cfg = scale_config()

        self.grid_rows = 1
        self.grid_cols = 1
        self.dataflow = 'os'

        # Stats objects
        self.stats_compute_cycles = np.ones(1) * -1
        self.stats_ifmap_dram_reads = np.ones(1) * -1
        self.stats_ifmap_dram_start_cycl = np.ones(1) * -1
        self.stats_ifmap_dram_end_cycl = np.ones(1) * -1

        self.stats_filter_dram_reads = np.ones(1) * -1
        self.stats_filter_dram_start_cycl = np.ones(1) * -1
        self.stats_filter_dram_end_cycl = np.ones(1) * -1

        self.stats_ofmap_dram_reads = np.ones(1) * -1
        self.stats_ofmap_dram_start_cycl = np.ones(1) * -1
        self.stats_ofmap_dram_end_cycl = np.ones(1) * -1

        self.overall_compute_cycles_per_layers = []
        self.overall_util_perc_per_layer = []

        self.overall_compute_cycles_all_layers = 0
        self.overall_util_perc_all_layer = 0

        self.total_ifmap_dram_reads = []
        self.total_filter_dram_reads = []
        self.total_ofmap_dram_writes = []

        # Flags
        self.params_valid = False
        self.all_grids_done = False
        self.metrics_ready = False

    #
    def set_params(self,
                    #topology_filename='./files/tutorial3_topofile.csv',
                    topology_filename='./topologies/conv_nets/test.csv',
                    single_arr_config_file='./files/single_arr_config.cfg',
                    grid_rows=1, grid_cols=1,
                    dataflow = 'os'
                    ):

        # Blank 1. Read the input files 
        # <insert code here>
        self.topo_obj = topologies()
        self.topo_obj.load_arrays(topology_filename)
        num_layers = self.topo_obj.get_num_layers()

        self.single_arr_cfg = scale_config()
        self.single_arr_cfg.read_conf_file(single_arr_config_file)

        self.grid_rows = grid_rows
        self.grid_cols = grid_cols

        num_arrays = grid_rows * grid_cols
        self.stats_compute_cycles = np.ones((num_layers, num_arrays)) * -1

        self.stats_ifmap_dram_reads = np.ones((num_layers, num_arrays)) * -1
        self.stats_ifmap_dram_start_cycl = np.ones((num_layers, num_arrays)) * -1
        self.stats_ifmap_dram_end_cycl = np.ones((num_layers, num_arrays)) * -1

        self.stats_filter_dram_reads = np.ones((num_layers, num_arrays)) * -1
        self.stats_filter_dram_start_cycl = np.ones((num_layers, num_arrays)) * -1
        self.stats_filter_dram_end_cycl = np.ones((num_layers, num_arrays)) * -1

        self.stats_ofmap_dram_writes = np.ones((num_layers, num_arrays)) * -1
        self.stats_ofmap_dram_start_cycl = np.ones((num_layers, num_arrays)) * -1
        self.stats_ofmap_dram_end_cycl = np.ones((num_layers, num_arrays)) * -1

        self.total_ifmap_dram_reads = []
        self.total_filter_dram_reads = []
        self.total_ofmap_dram_writes = []

        self.overall_compute_cycles_per_layers = []
        self.overall_util_perc_per_layer = []

        self.overall_compute_cycles_all_layers = 0
        self.overall_util_perc_all_layer = 0

        self.dataflow = dataflow
        self.params_valid = True

    #
    def run_simulation_single_layer(self, layer_id=0):

        # Blank 2. Create the operand matrices
        # <Insert code here>
        opmat_obj = opmat()
        opmat_obj.set_params(config_obj=self.single_arr_cfg, topoutil_obj=self.topo_obj, layer_id=layer_id)

        _, ifmap_op_mat = opmat_obj.get_ifmap_matrix()
        _, filter_op_mat = opmat_obj.get_filter_matrix()
        _, ofmap_op_mat = opmat_obj.get_ofmap_matrix()

        for grid_row_id in range(self.grid_rows):
            for grid_col_id in range(self.grid_cols):

                arr_id = grid_row_id * self.grid_cols + grid_col_id
                print('Running subarray ' + str(arr_id))

                ifmap_op_mat_part, filter_op_mat_part, ofmap_op_mat_part =\
                    self.get_opmat_parts(ifmap_op_mat, filter_op_mat, ofmap_op_mat,
                                         grid_row_id, grid_col_id)

                # Blank 3. Instantiate the mapping utilities
                #<Insert code here>
                compute_system = systolic_compute_os()
                if self.dataflow == 'ws':
                    compute_system = systolic_compute_ws()
                elif self.dataflow == 'is':
                    compute_system = systolic_compute_is()

                compute_system.set_params(config_obj=self.single_arr_cfg,
                                          ifmap_op_mat=ifmap_op_mat_part,
                                          filter_op_mat=filter_op_mat_part,
                                          ofmap_op_mat=ofmap_op_mat_part)

                ifmap_demand_mat, filter_demand_mat, ofmap_demand_mat = compute_system.get_demand_matrices()

                # Blank 4. Memory system
                #<Insert code here>
                memory_system = mem_dbsp()

                ifmap_buf_size_kb, filter_buf_size_kb, ofmap_buf_size_kb = self.single_arr_cfg.get_mem_sizes()
                ifmap_buf_size_bytes = 1024 * ifmap_buf_size_kb
                filter_buf_size_bytes = 1024 * filter_buf_size_kb
                ofmap_buf_size_bytes = 1024 * ofmap_buf_size_kb

                arr_row, arr_col = self.single_arr_cfg.get_array_dims()

                ifmap_backing_bw = 1
                filter_backing_bw = 1
                ofmap_backing_bw = 1
                if self.dataflow == 'os' or self.dataflow == 'ws':
                    ifmap_backing_bw = arr_row
                    filter_backing_bw = arr_col
                    ofmap_backing_bw = arr_col

                elif self.dataflow == 'is':
                    ifmap_backing_bw = arr_col
                    filter_backing_bw = arr_row
                    ofmap_backing_bw = arr_col

                memory_system.set_params(
                    word_size=1,
                    ifmap_buf_size_bytes=ifmap_buf_size_bytes,
                    filter_buf_size_bytes=filter_buf_size_bytes,
                    ofmap_buf_size_bytes=ofmap_buf_size_bytes,
                    rd_buf_active_frac=0.5, wr_buf_active_frac=0.5,
                    ifmap_backing_buf_bw=ifmap_backing_bw,
                    filter_backing_buf_bw=filter_backing_bw,
                    ofmap_backing_buf_bw=ofmap_backing_bw,
                    verbose=True,
                    estimate_bandwidth_mode=True
                )

                memory_system.service_memory_requests(ifmap_demand_mat, filter_demand_mat, ofmap_demand_mat)

                self.gather_stats(row_id=grid_row_id,
                                  col_id=grid_col_id,
                                  memory_system_obj=memory_system,
                                  layer_id=layer_id)

        self.all_grids_done = True

    #
    def run_simulations_all_layers(self):
        assert self.params_valid, 'Params are not valid'

        for lid in range(self.topo_obj.get_num_layers()):
            print('Running layer=' + str(lid))
            self.run_simulation_single_layer(lid)

    #
    def get_opmat_parts(self, ifmap_op_mat, filter_op_mat, ofmap_op_mat,
                        grid_row_id, grid_col_id):

        ifmap_op_mat_part = np.zeros((1,1))
        filter_op_mat_part = np.zeros((1,1))
        ofmap_op_mat_part = np.zeros((1,1))

        if self.dataflow == 'os':
            ifmap_rows_per_part = math.ceil(ifmap_op_mat.shape[0] / self.grid_rows)
            ifmap_row_start_id = grid_row_id * ifmap_rows_per_part
            ifmap_row_end_id = min(ifmap_row_start_id + ifmap_rows_per_part, ifmap_op_mat.shape[0]-1)
            ifmap_op_mat_part = ifmap_op_mat[ifmap_row_start_id:ifmap_row_end_id, :]

            filter_cols_per_part = math.ceil(filter_op_mat.shape[1] / self.grid_cols)
            filter_col_start_id = grid_col_id * filter_cols_per_part
            filter_col_end_id = min(filter_col_start_id + filter_cols_per_part, filter_op_mat.shape[1]-1)
            filter_op_mat_part = filter_op_mat[:, filter_col_start_id:filter_col_end_id]

            ofmap_rows_per_part = math.ceil(ofmap_op_mat.shape[0]/ self.grid_rows)
            ofmap_row_start_id = grid_row_id * ofmap_rows_per_part
            ofmap_row_end_id = min(ofmap_row_start_id + ofmap_rows_per_part, ofmap_op_mat.shape[0]-1)

            ofmap_cols_per_part = math.ceil(ofmap_op_mat.shape[1] / self.grid_cols)
            ofmap_col_start_id = grid_col_id * ofmap_cols_per_part
            ofmap_col_end_id = min(ofmap_col_start_id + ofmap_cols_per_part, ofmap_op_mat.shape[1]-1)
            ofmap_op_mat_part = ofmap_op_mat[ofmap_row_start_id: ofmap_row_end_id,
                                             ofmap_col_start_id: ofmap_col_end_id]

        elif self.dataflow == 'ws':
            ifmap_cols_per_part = math.ceil(ifmap_op_mat.shape[1] / self.grid_cols)
            ifmap_col_start_id = grid_col_id * ifmap_cols_per_part
            ifmap_col_end_id = min(ifmap_col_start_id + ifmap_cols_per_part, ifmap_op_mat.shape[1]-1)
            ifmap_op_mat_part = ifmap_op_mat[:,ifmap_col_start_id:ifmap_col_end_id]

            filter_rows_per_part = math.ceil(filter_op_mat.shape[0] / self.grid_rows)
            filter_row_start_id = grid_row_id * filter_rows_per_part
            filter_row_end_id = min(filter_row_start_id + filter_rows_per_part, filter_op_mat.shape[0]-1)

            filter_cols_per_part = math.ceil(filter_op_mat.shape[1] / self.grid_cols)
            filter_col_start_id = grid_col_id * filter_cols_per_part
            filter_col_end_id = min(filter_col_start_id + filter_cols_per_part, filter_op_mat.shape[1]-1)

            filter_op_mat_part = filter_op_mat[ filter_row_start_id:filter_row_end_id,
                                                filter_col_start_id:filter_col_end_id]

            ofmap_cols_per_part = math.ceil(ofmap_op_mat.shape[1] / self.grid_cols)
            ofmap_col_start_id = grid_col_id * ofmap_cols_per_part
            ofmap_col_end_id = min(ofmap_col_start_id + ofmap_cols_per_part, ofmap_op_mat.shape[1]-1)
            ofmap_op_mat_part = ofmap_op_mat[:, ofmap_col_start_id: ofmap_col_end_id]

        elif self.dataflow == 'is':
            ifmap_rows_per_part = math.ceil(ifmap_op_mat.shape[0] / self.grid_rows)
            ifmap_row_start_id = grid_row_id * ifmap_rows_per_part
            ifmap_row_end_id = min(ifmap_row_start_id + ifmap_rows_per_part, ifmap_op_mat.shape[0]-1)

            ifmap_cols_per_part = math.ceil(ifmap_op_mat.shape[1] / self.grid_cols)
            ifmap_col_start_id = grid_col_id * ifmap_cols_per_part
            ifmap_col_end_id = min(ifmap_col_start_id + ifmap_cols_per_part, ifmap_op_mat.shape[1]-1)
            ifmap_op_mat_part = ifmap_op_mat[ifmap_row_start_id:ifmap_row_end_id,
                                             ifmap_col_start_id:ifmap_col_end_id]

            filter_rows_per_part = math.ceil(filter_op_mat.shape[0] / self.grid_rows)
            filter_row_start_id = grid_row_id * filter_rows_per_part
            filter_row_end_id = min(filter_row_start_id + filter_rows_per_part, filter_op_mat.shape[0]-1)

            filter_op_mat_part = filter_op_mat[filter_row_start_id:filter_row_end_id,:]

            ofmap_rows_per_part = math.ceil(ofmap_op_mat.shape[0] / self.grid_rows)
            ofmap_row_start_id = grid_row_id * ofmap_rows_per_part
            ofmap_row_end_id = min(ofmap_row_start_id + ofmap_rows_per_part, ofmap_op_mat.shape[0]-1)

            ofmap_op_mat_part = ofmap_op_mat[ofmap_row_start_id: ofmap_row_end_id, :]

        return ifmap_op_mat_part, filter_op_mat_part, ofmap_op_mat_part

    #
    def gather_stats(self, memory_system_obj, row_id, col_id, layer_id):
        # Stats to gather
        indx = row_id * self.grid_cols + col_id

        # 1. Compute cycles
        self.stats_compute_cycles[layer_id, indx] = memory_system_obj.get_total_compute_cycles()

        # 2. Bandwidth requirements
        ifmap_start_cycle, ifmap_end_cycle, ifmap_dram_reads = memory_system_obj.get_ifmap_dram_details()
        filter_start_cycle, filter_end_cycle, filter_dram_reads = memory_system_obj.get_filter_dram_details()
        ofmap_start_cycle, ofmap_end_cycle, ofmap_dram_writes = memory_system_obj.get_ofmap_dram_details()

        self.stats_ifmap_dram_reads[layer_id, indx] = ifmap_dram_reads
        self.stats_filter_dram_reads[layer_id, indx] = filter_dram_reads
        self.stats_ofmap_dram_writes[layer_id, indx] = ofmap_dram_writes

        self.stats_ifmap_dram_start_cycl[layer_id, indx] = ifmap_start_cycle
        self.stats_filter_dram_start_cycl[layer_id, indx] = filter_start_cycle
        self.stats_ofmap_dram_start_cycl[layer_id, indx] = ofmap_start_cycle

        self.stats_ifmap_dram_end_cycl[layer_id, indx] = ifmap_end_cycle
        self.stats_filter_dram_end_cycl[layer_id, indx] = filter_end_cycle
        self.stats_ofmap_dram_end_cycl[layer_id, indx] = ofmap_end_cycle

    #
    def calc_overall_stats_all_layer(self):
        assert self.all_grids_done, 'Not all data is available'

        num_layers = self.topo_obj.get_num_layers()
        for layer_id in range(num_layers):
            # 1. Compute cycles
            this_layer_compute_cycles = max(self.stats_compute_cycles[layer_id])
            self.overall_compute_cycles_per_layers += [this_layer_compute_cycles]

            # 2. Overall utilization
            num_compute = self.topo_obj.get_layer_num_ofmap_px(layer_id=layer_id) \
                          * self.topo_obj.get_layer_window_size(layer_id=layer_id)

            row, col = self.single_arr_cfg.get_array_dims()
            total_compute_possible = self.grid_cols * self.grid_rows * row * col * this_layer_compute_cycles
            this_layer_overall_util_perc = num_compute / total_compute_possible * 100

            self.overall_util_perc_per_layer += [this_layer_overall_util_perc]

            # 3. Memory stats
            self.total_ifmap_dram_reads += [sum(self.stats_ifmap_dram_reads[layer_id])]
            self.total_filter_dram_reads += [sum(self.stats_filter_dram_reads[layer_id])]
            self.total_ofmap_dram_writes += [sum(self.stats_ofmap_dram_writes[layer_id])]

        self.overall_compute_cycles_all_layers = sum(self.overall_compute_cycles_per_layers)
        self.overall_util_perc_all_layer = sum(self.overall_util_perc_per_layer) / num_layers

        self.metrics_ready = True

    #
    def get_report_items(self):
        return self.overall_compute_cycles_all_layers, self.overall_util_perc_all_layer, \
               self.total_ifmap_dram_reads[0], self.total_filter_dram_reads[0], self.total_ofmap_dram_writes[0]

#
def plot_stacked_bar(x, y_series_np, legends, title, y_axis_label=''):
    num_plots = y_series_np.shape[0]
    plt.bar(x, y_series_np[0], label=legends[0])
    bottom = y_series_np[0]
    for plt_id in range(1, num_plots):
        plt.bar(x, y_series_np[plt_id], bottom=bottom,label=legends[plt_id])
        bottom += y_series_np[plt_id]

    plt.ylabel(y_axis_label)
    plt.title(title)
    plt.xticks(rotation=70)
    plt.legend()

    plt.show()

#
if __name__ == '__main__':

    #topofile = './files/tutorial3_topofile.csv'
    topofile = ['./topologies/conv_nets/test.csv', './topologies/conv_nets/test.csv']
    config_file = './configs/scale.cfg'

    x_labels = ['2x2', '1x4', '4x1']

    # Run 2x2 grid
    print("Running 2x2 grid")
    grid1 = scaled_out_simulator()
    grid1.set_params(topology_filename=topofile[0],
                     single_arr_config_file=config_file,
                     grid_rows=2, grid_cols=2, dataflow='os')

    grid1.run_simulations_all_layers()
    grid1.calc_overall_stats_all_layer()

    cycles, util, ifmap_read, filter_reads, ofmap_writes = grid1.get_report_items()
    all_cycles = [cycles]
    all_utils = [util]
    dram_arr = [[ifmap_read, filter_reads, ofmap_writes]]


    # Run 1x4 grid
    print("Running 1x4 grid")
    grid2 = scaled_out_simulator()
    grid2.set_params(topology_filename=topofile[0],
                     single_arr_config_file=config_file,
                     grid_rows=1, grid_cols=4, dataflow='os')

    grid2.run_simulations_all_layers()
    grid2.calc_overall_stats_all_layer()

    cycles, util, ifmap_read, filter_reads, ofmap_writes = grid2.get_report_items()
    all_cycles += [cycles]
    all_utils += [util]
    dram_arr += [[ifmap_read, filter_reads, ofmap_writes]]


    # Run grid 4x1
    print("Running 4x1 grid")
    grid3 = scaled_out_simulator()
    grid3.set_params(topology_filename=topofile[0],
                     single_arr_config_file=config_file,
                     grid_rows=4, grid_cols=1, dataflow='os')

    grid3.run_simulations_all_layers()
    grid3.calc_overall_stats_all_layer()

    cycles, util, ifmap_read, filter_reads, ofmap_writes = grid3.get_report_items()
    all_cycles += [cycles]
    all_utils += [util]
    dram_arr += [[ifmap_read, filter_reads, ofmap_writes]]

    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()

    ax1.bar(x_labels, all_cycles)
    ax2.plot(x_labels, all_utils, 'ro--')

    ax1.set_ylabel('Cycles')
    ax2.set_ylabel('Util%')
    plt.title('Runtime and Utilization in Scale-out')

    plt.show()

    access_counts = np.asarray(dram_arr).reshape((3,3))
    access_counts = np.transpose(access_counts)

    plot_stacked_bar(x_labels, y_series_np=access_counts, legends=['DRAM_IFMAP', 'DRAM_FILTER', 'DRAM_OFMAP'],
                     title='DRAM accesses', y_axis_label='Num access')

