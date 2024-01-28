from envs.utils import Order


def rl_policy(args, model, obs, info):
    pass

def base_taker_policy(obs, info):
    x1 = 0.8
    if obs['signal0'] > x1:

        # Long opening
        price = (obs['ap0'] + obs['bp0']) / 2 * (1 + (obs['signal0'] * 0.0001))
        if price < obs['ap0']:
            order = Order(side=1, price=0, volume=0)
        if obs['ap0'] <= price:
            order = Order(side=0, price=price, volume=min(obs['av0'], 300 - info['code_net_position']))
            #挂单买，买入量为卖一量，或者300-持仓量（不能超过300的阈值）
    elif obs['signal0'] < -x1:

        # Short opening
        price = (obs['ap0'] + obs['bp0']) / 2 * (1 + (obs['signal0'] * 0.0001))
        if price > obs['bp0']:
            order = Order(side=1, price=0, volume=0)
        if obs['bp0'] >= price:
            order = Order(side=2, price=price, volume=min(obs['bv0'], 300 + info['code_net_position'])) 
            #挂单卖，卖出量为买一量，或者300+持仓量（不能超过300的阈值）

    else: #obs['signal0']在[-x1,x1]之间，视作无明显信号
        order = Order(side=1, price=0, volume=0)

    return order