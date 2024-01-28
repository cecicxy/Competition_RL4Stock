import argparse
import json
import multiprocessing
import os
import random
from pprint import PrettyPrinter

import numpy as np

from backtest.backtest_oneday import backtest_oneday
from backtest.utils import BacktestMetrics, BacktestStats, ParquetFile
from envs.stock_base_env_cython import StockBaseEnvCython
from mock_market_common.mock_market_data_cython import MockMarketDataCython


def backtest(logdir, TEST_WHITE_CORE_STRATEGY):
    if TEST_WHITE_CORE_STRATEGY:
        args = None
        model = None
    else:
        pass

    for backtest_mode in ['twoSides']:

        if not os.path.exists(f"{logdir}/backtest_{backtest_mode}"):
            os.makedirs(f"{logdir}/backtest_{backtest_mode}")

        SEED = 1024
        os.environ["PYTHONHASHSEED"] = str(SEED)
        np.random.seed(SEED)
        random.seed(SEED)

        # Init Env
        file = ParquetFile()

        # dateList = args.test_date_list
        signal_file_original_rootpath = './data'
        dateList = [name for name in os.listdir(signal_file_original_rootpath) if
                    os.path.isdir(os.path.join(signal_file_original_rootpath, name))] # 获取文件夹下的所有文件名
        dateList.sort() #文件按其日期名称排序

        envs = []
        for date in dateList[:]:
            file.filename = "./data/" + date + '/train_data.parquet'
            file.load()
            df = file.data
            code_list = []
            for item in df['code'].unique():
                code_list.append(float(item)) #从numpy.float64转换为python的float格式
            df = np.array(df)
            mock_market_data = MockMarketDataCython(df) #经过 Cython 封装的数据读取模块
            env = StockBaseEnvCython(date, code_list, mock_market_data) #经过 Cython 封装的环境模块
            envs.append(env)

        backtest_datas = multiprocessing.Manager().list() #创建一个可以在多个进程间共享和传递的列表，用于存储每日的回测指标
        processes = []
        for environment in envs:
            process = multiprocessing.Process(target=backtest_oneday,
                                              args=(environment, logdir, backtest_mode,
                                                    TEST_WHITE_CORE_STRATEGY, backtest_datas)) #多进程回测，backtest_datas也被传入
            processes.append(process)

        for process in processes:
            process.start()

        for process in processes:
            process.join()

        backtest_metrics = BacktestMetrics(envs, backtest_datas) 
        backtest_metrics.make(logdir) #拼接每日的回测指标，生成backtest_metrics.csv文件
        pp = PrettyPrinter(width=200) #创建一个 PrettyPrinter 对象，用于打印回测指标
        pp.pprint(backtest_metrics.data) #打印回测指标

        backtest_stats = BacktestStats(backtest_metrics.data)
        backtest_stats.make() #计算回测指标的统计量，生成backtest_stats.csv文件
        pp.pprint(backtest_stats.data)
        print(backtest_stats.data['daily_pnl_mean_sharped']) #比赛规定的最终收益的计算值


if __name__ == "__main__":
    print('Start backtesting...')
    TEST_WHITE_CORE_STRATEGY = True
    if TEST_WHITE_CORE_STRATEGY:
        logdir = "./backtest/basic_policy_log/"
    else:
        # TODO:Add code to test your reinforcement learning model
        pass
    backtest(logdir, TEST_WHITE_CORE_STRATEGY)
