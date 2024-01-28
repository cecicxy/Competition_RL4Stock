from backtest.policies import base_taker_policy
from backtest.utils import time_format_conversion
from envs.utils import Order


def backtest_oneday(environment, logdir, backtest_mode, TEST_WHITE_CORE_STRATEGY, backtest_datas):
    obs, done, info = environment.reset() #重置为.parquet文件中某支股票的初始行情信息
    while True:

        if ((53820 - time_format_conversion(obs['eventTime'])) / 5) < (
                abs(environment.code_net_position - 0) + 1): 
# 53820 为 15:00:00 的时间戳,检查是否接近市场收盘时间，如果是，则执行平仓操作；否则，继续根据策略产生订单。
# 卖出平仓：指持有多头头寸（即持有该资产，希望价格上涨获利）的情况下，通过卖出该资产结束持仓。这种操作也称为“平多”或  “平多头”。
# 买入平仓：指持有空头头寸（即卖空该资产，希望价格下跌获利）的情况下，通过买入该资产结束持仓。这种操作也称为“平空”或“平空头”。
# 平仓操作通常发生在投资者已经达到预期收益、需要止损、调整头寸或者交易策略发生变化等情况下。

            # Close positions near the market close.
            if backtest_mode == 'oneSide': #单向交易，只能卖出
                order = Order(side=2, volume=min(
                    1, obs['bv0']), price=obs['bp0'] - 0.1) #只比市场买一价低0.1元的价格卖出，
                #volume=min(1, obs['bv0'])：a safeguard against potential data errors or unexpected situations
            elif backtest_mode == 'twoSides': #双向交易，可以买入和卖出
                if environment.code_net_position > 0:
                    order = Order(side=2, volume=min(
                        1, obs['bv0']), price=obs['bp0'] - 0.1)
                elif environment.code_net_position < 0:
                    order = Order(side=0, volume=min(
                        1, obs['av0']), price=obs['ap0'] + 0.1)
                else:
                    order = Order(side=1, volume=0, price=0)
        else:
            order = base_taker_policy(obs, info)
            # if order.side != 1:
            #     print(order)

        obs, done, info = environment.step(order)

        if done == 2:
            # done == 2 indicates the end of trading for a particular stock on that day;
            # after reset, trading begins for the next stock
            obs, done, info = environment.reset()

        if done == 1:
            # done == 1 indicates the completion of trading for all stocks on that day.
            break

    backtest_datas.append(environment.get_backtest_metric())

    # # Save the back test information locally
    # environment.dump(f"{logdir}/backtest_{backtest_mode}/{environment.date}.json")
