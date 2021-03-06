#!/usr/bin/python3

import pytest
from brownie import network, Contract, Wei, chain


@pytest.fixture(scope="module")
def requireMainnetFork():
    assert (network.show_active() == "mainnet-fork" or network.show_active() == "mainnet-fork-alchemy")


@pytest.fixture(scope="module")
def setFeesController(bzx, stakingV1, accounts):
    bzx.setFeesController(stakingV1, {"from": bzx.owner()})
    assets = [
        "0x56d811088235F11C8920698a204A5010a788f4b3",  # BZRX
        "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
        "0x6B175474E89094C44Da98b954EedeAC495271d0F",  # DAI
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
        "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
        "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",  # WBTC
        "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",  # AAVE
        "0xdd974D5C2e2928deA5F71b9825b8b646686BD200",  # KNC
        "0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2",  # MKR
        "0x514910771AF9Ca656af840dff83E8264EcF986CA",  # LINK
        "0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e",  # YFI
    ]
    bzx.withdrawFees(assets, accounts[8], 0, {'from': stakingV1})


@pytest.fixture(scope="module")
def LPT(accounts, TestToken):
    LPT = loadContractFromAbi(
        "0xe26A220a341EAca116bDa64cF9D5638A935ae629", "LPT", TestToken.abi)
    return LPT


@pytest.fixture(scope="module")
def vBZRX(accounts, BZRXVestingToken):
    vBZRX = loadContractFromAbi(
        "0xb72b31907c1c95f3650b64b2469e08edacee5e8f", "vBZRX", BZRXVestingToken.abi)
    vBZRX.transfer(accounts[0], 1000*10**18, {'from': vBZRX.address})
    return vBZRX


@pytest.fixture(scope="module")
def iUSDC(accounts, LoanTokenLogicStandard):
    iUSDC = loadContractFromAbi(
        "0x32E4c68B3A4a813b710595AebA7f6B7604Ab9c15", "iUSDC", LoanTokenLogicStandard.abi)
    return iUSDC


@pytest.fixture(scope="module")
def WETH(accounts, TestWeth):
    WETH = loadContractFromAbi(
        "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", "WETH", TestWeth.abi)
    return WETH


@pytest.fixture(scope="module")
def USDC(accounts, TestToken):
    USDC = loadContractFromAbi(
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "USDC", TestToken.abi)
    return USDC


@pytest.fixture(scope="module")
def BZRX(accounts, TestToken):
    BZRX = loadContractFromAbi(
        "0x56d811088235F11C8920698a204A5010a788f4b3", "BZRX", TestToken.abi)
    BZRX.transfer(accounts[0], 1000*10**18, {'from': BZRX.address})
    return BZRX


@pytest.fixture(scope="module")
def iBZRX(accounts, BZRX, LoanTokenLogicStandard):
    iBZRX = loadContractFromAbi(
        "0x18240BD9C07fA6156Ce3F3f61921cC82b2619157", "iBZRX", LoanTokenLogicStandard.abi)
    BZRX.approve(iBZRX, 10*10**50, {'from': accounts[0]})
    iBZRX.mint(accounts[0], 100*10**18, {'from': accounts[0]})
    return iBZRX


# def loadContractFromEtherscan(address, alias):
#     try:
#         return Contract(alias)
#     except ValueError:
#         contract = Contract.from_explorer(address)
#         contract.set_alias(alias)
#         return contract


def loadContractFromAbi(address, alias, abi):
    try:
        return Contract(alias)
    except ValueError:
        contract = Contract.from_abi(alias, address=address, abi=abi)
        return contract


# TODO add LPToken
def testStake_UnStake(requireMainnetFork, stakingV1, bzx, setFeesController, BZRX, vBZRX, iBZRX, accounts):
    # tx =
    # tx.info()
    balanceOfBZRX = BZRX.balanceOf(accounts[0])
    balanceOfvBZRX = vBZRX.balanceOf(accounts[0])
    balanceOfiBZRX = iBZRX.balanceOf(accounts[0])

    BZRX.approve(stakingV1, balanceOfBZRX, {'from': accounts[0]})
    vBZRX.approve(stakingV1, balanceOfvBZRX, {'from': accounts[0]})
    iBZRX.approve(stakingV1, balanceOfiBZRX, {'from': accounts[0]})
    tokens = [BZRX, vBZRX, iBZRX]
    amounts = [balanceOfBZRX, balanceOfvBZRX, balanceOfiBZRX]
    tx = stakingV1.stake(
        tokens, amounts)
    # tx.info()
    # print("tx", tx.events)

    balanceOfBZRXAfter = BZRX.balanceOf(accounts[0])
    balanceOfvBZRXAfter = vBZRX.balanceOf(accounts[0])
    balanceOfiBZRXAfter = iBZRX.balanceOf(accounts[0])

    # due to vesting starated we have small balance vested
    assert(balanceOfBZRXAfter > 0 and balanceOfBZRXAfter/10**18 < 1)
    assert(balanceOfvBZRXAfter == 0)
    assert(balanceOfiBZRXAfter == 0)

    stakedEvents = tx.events['Stake']
    for index, stakedEvent in enumerate(stakedEvents, 0):
        assert(stakedEvent['user'] == accounts[0])
        assert(stakedEvent['token'] == tokens[index])
        assert(stakedEvent['delegate'] == accounts[0])
        assert(stakedEvent['amount'] == amounts[index])

    transferEvents = tx.events['Transfer']
    i = 0  # due to extra event transfer does not allighn
    for index, transferEvent in enumerate(transferEvents, 0):
        # most probably a bug in brownie not doing orderdic properly for events
        if (transferEvent['from'] == accounts[i]):
            assert(transferEvent['from'] == accounts[i])
            assert(transferEvent['to'] == stakingV1)
            assert(transferEvent['value'] == amounts[i])
            i += 1

    tx = stakingV1.unstake(tokens, amounts)
    # tx.info()

    unStakedEvents = tx.events['Unstake']
    for index, unStakedEvent in enumerate(unStakedEvents, 0):
        assert(unStakedEvent['user'] == accounts[0])
        assert(unStakedEvent['token'] == tokens[index])
        assert(unStakedEvent['delegate'] == accounts[0])
        assert(unStakedEvent['amount'] == amounts[index])

    transferEvents = tx.events['Transfer']
    i = 0  # due to extra event transfer does not allighn
    for index, transferEvent in enumerate(transferEvents, 0):
        # most probably a bug in brownie not doing orderdic properly for events
        if (transferEvent['from'] == accounts[i]):
            assert(transferEvent['from'] == stakingV1)
            assert(transferEvent['to'] == accounts[0])
            assert(transferEvent['value'] == amounts[index])
            i += 1

    assert True

# delegate was removed for now
# def testStake_UnStake_WithDelegate(requireMainnetFork, stakingV1, bzx, setFeesController, BZRX, vBZRX, iBZRX, accounts):
#     # tx =
#     # tx.info()
#     balanceOfBZRX = BZRX.balanceOf(accounts[0])
#     balanceOfvBZRX = vBZRX.balanceOf(accounts[0])
#     balanceOfiBZRX = iBZRX.balanceOf(accounts[0])

#     BZRX.approve(stakingV1, balanceOfBZRX, {'from': accounts[0]})
#     vBZRX.approve(stakingV1, balanceOfvBZRX, {'from': accounts[0]})
#     iBZRX.approve(stakingV1, balanceOfiBZRX, {'from': accounts[0]})
#     tokens = [BZRX, vBZRX, iBZRX]
#     amounts = [balanceOfBZRX, balanceOfvBZRX, balanceOfiBZRX]
#     tx = stakingV1.stake(tokens, amounts)

#     tx = stakingV1.changeDelegate(accounts[1])

#     delegateChanged = tx.events['ChangeDelegate']
#     assert(delegateChanged['user'] == accounts[0])
#     assert(delegateChanged['oldDelegate'] ==
#            accounts[0])
#     assert(delegateChanged['newDelegate'] == accounts[1])

#     tx = stakingV1.unstake(tokens, amounts)
#     # tx.info()

#     unStakedEvents = tx.events['Unstake']
#     for index, unStakedEvent in enumerate(unStakedEvents, 0):
#         assert(unStakedEvent['user'] == accounts[0])
#         assert(unStakedEvent['token'] == tokens[index])
#         assert(unStakedEvent['delegate'] == accounts[1])
#         assert(unStakedEvent['amount'] == amounts[index])

#     transferEvents = tx.events['Transfer']
#     for index, transferEvent in enumerate(transferEvents, 0):
#         assert(transferEvent['from'] == stakingV1)
#         assert(transferEvent['to'] == accounts[0])
#         assert(transferEvent['value'] == amounts[index])

#     balances = stakingV1.balanceOfByAssets.call(accounts[0])
#     assert(balances[0] == 0)
#     assert(balances[1] == 0)
#     assert(balances[2] == 0)
#     assert(balances[3] == 0)
#     assert True


def testStake_SweeepFees(requireMainnetFork, stakingV1, bzx, setFeesController, BZRX, vBZRX, iBZRX, accounts, iUSDC, USDC):
    tx = stakingV1.sweepFees()
    withdrawFeesEvent = tx.events['WithdrawFees']
    assert(withdrawFeesEvent[0]['sender'] == accounts[0])

    convertFeesEvent = tx.events['ConvertFees']
    assert(convertFeesEvent[0]['sender'] == accounts[0])

    distributeFeesEvent = tx.events['DistributeFees']
    assert(distributeFeesEvent[0]['sender'] == accounts[0])

    assert True


def testStake_BZRXProfit(requireMainnetFork, stakingV1, bzx, setFeesController, BZRX, vBZRX, iBZRX, accounts, iUSDC, USDC, WETH):

    earnedAmounts = stakingV1.earned(accounts[0])
    assert(earnedAmounts == (0, 0, 0, 0))
    print("earnedAmounts", earnedAmounts)
    balanceOfBZRX = BZRX.balanceOf(accounts[0])

    BZRX.approve(stakingV1, balanceOfBZRX, {'from': accounts[0]})

    tokens = [BZRX, vBZRX, iBZRX]
    amounts = [100*10**18, 0, 0]
    tx = stakingV1.stake(tokens, amounts)

    # iUSDC.borrow(0, 100*10**18, 1*10**18, "0x0000000000000000000000000000000000000000", accounts[0], accounts[0], {'value': Wei("1 ether")})
    borrowAmount = 100*10**6
    borrowTime = 7884000
    collateralAmount = 1*10**18
    collateralAddress = "0x0000000000000000000000000000000000000000"
    txBorrow = iUSDC.borrow("", borrowAmount, borrowTime, collateralAmount, collateralAddress,
                            accounts[0], accounts[0], b"", {'from': accounts[0], 'value': Wei(collateralAmount)})

    payBorrowingFeeEvent = filterEvents(
        '0xfb6c38ae4fdd498b3a5003f02ca4ca5340dfedb36b1b100c679eb60633b2c0a7', txBorrow.events)
    payBorrowingFeeAmount = int(str(payBorrowingFeeEvent['data']), 0)

    payLendingFeeEvent = filterEvents(
        '0x40a75ae5f7a5336e75f7c7977e12c4b46a9ac0f30de01a2d5b6c1a4f4af63587', txBorrow.events)
    payLendingFeeAmount = int(str(payLendingFeeEvent['data']), 0)

    txSweep = stakingV1.sweepFees()

    borrowFee = txSweep.events['WithdrawBorrowingFees'][0]
    assert(borrowFee['sender'] == stakingV1)
    assert(borrowFee['token'] == WETH)
    assert(borrowFee['sender'] == stakingV1)
    assert(borrowFee['amount'] == payBorrowingFeeAmount)

    lendingFee = txSweep.events['WithdrawLendingFees'][0]
    assert(lendingFee['sender'] == stakingV1)
    assert(lendingFee['token'] == USDC)
    assert(lendingFee['sender'] == stakingV1)
    assert(lendingFee['amount'] == payLendingFeeAmount)

    assert(txSweep.events['AddRewards'][0]['sender'] == accounts[0])
    bzrxAmount = txSweep.events['AddRewards'][0]['bzrxAmount']
    stableCoinAmount = txSweep.events['AddRewards'][0]['stableCoinAmount']

    assert(txSweep.events['DistributeFees'][0]['sender'] == accounts[0])
    bzrxRewards = txSweep.events['DistributeFees'][0]['bzrxRewards']
    stableCoinRewards = txSweep.events['DistributeFees'][0]['stableCoinRewards']

    assert(bzrxAmount == bzrxRewards)
    assert(stableCoinAmount == stableCoinRewards)
    earned = stakingV1.earned(accounts[0])

    # we have roundings for last 1 digit
    print("roundings bzrx", str(bzrxRewards), str(earned[0]))
    assert(bzrxRewards - earned[0] <= 1)
    # we have roundings for last 1 digit
    print("roundings stableCoin", str(stableCoinAmount), str(earned[1]))
    assert(stableCoinAmount - earned[1] <= 1)

    #stakingV1.claim(False, {'from': accounts[0]})
    #earned = stakingV1.earned(accounts[0])

    # second user staking. he should get zero rewards if he just staked
    earnedAmounts = stakingV1.earned(accounts[1])
    assert(earnedAmounts == (0, 0, 0, 0))
    BZRX.transfer(accounts[1], 1000*10**18, {'from': BZRX.address})

    balanceOfBZRX = BZRX.balanceOf(accounts[1])

    BZRX.approve(stakingV1, balanceOfBZRX, {'from': accounts[1]})

    tokens = [BZRX, vBZRX, iBZRX]
    amounts2 = [100*10**18, 0, 0]
    tx = stakingV1.stake(
        tokens, amounts2, {'from': accounts[1]})

    earnedAmounts = stakingV1.earned(accounts[1])
    print(str(earnedAmounts))
    assert(earnedAmounts == (0, 0, 0, 0))

    txBorrow = iUSDC.borrow("", borrowAmount, borrowTime, collateralAmount, collateralAddress,
                            accounts[0], accounts[0], b"", {'from': accounts[0], 'value': Wei(collateralAmount)})

    txSweepSecondAcc = stakingV1.sweepFees()

    print(str(amounts), str(amounts2))
    assert(amounts[0] == amounts2[0])
    assert(stakingV1.balanceOfStored(
        accounts[0]) == stakingV1.balanceOfStored(accounts[1]))

    '''
    earnedAfter = stakingV1.earned(accounts[0])
    earned1After = stakingV1.earned(accounts[1])
    print("account[0] before", str(earned[0]))
    print("account[0] after", str(earnedAfter[0] - earned[0]))
    print("account[1] after", str(earned1After[0]))
    print("diff", str(earned1After[0] - earnedAfter[0] + earned[0]))
    '''

    assert True


def filterEvents(topic, events):
    for event in events:
        for key in event.keys():
            if key == 'topic1':
                if event[key] == topic:
                    payBorrowingFeeEvent = event
                    break
    return payBorrowingFeeEvent


def testStake_VestingFees(requireMainnetFork, stakingV1, bzx, setFeesController, BZRX, vBZRX, iBZRX, accounts, iUSDC, USDC, WETH):
    balanceOfvBZRX = vBZRX.balanceOf(accounts[0])
    vBZRX.approve(stakingV1, balanceOfvBZRX, {'from': accounts[0]})
    stakingV1.stake([vBZRX], [balanceOfvBZRX])

    # borrowing to make fees
    borrowAmount = 100*10**6
    borrowTime = 7884000
    collateralAmount = 1*10**18
    collateralAddress = "0x0000000000000000000000000000000000000000"
    txBorrow = iUSDC.borrow("", borrowAmount, borrowTime, collateralAmount, collateralAddress,
                            accounts[0], accounts[0], b"", {'from': accounts[0], 'value': Wei(collateralAmount)})

    sweepTx = stakingV1.sweepFees()

    earningsDuringVesting = stakingV1.earned(accounts[0])
    # vesting already started
    assert(earningsDuringVesting[0] >
           0 and earningsDuringVesting[0]/10**18 < 1)
    assert(earningsDuringVesting[1] > 0)
    assert(earningsDuringVesting[2] > 0)
    assert(earningsDuringVesting[3] > 0)
    totalVestingFeesBzrx = earningsDuringVesting[2]
    totalVestingFees3Poll = earningsDuringVesting[3]

    # moving time after vesting end
    chain.sleep(vBZRX.vestingEndTimestamp() - chain.time() + 100)
    chain.mine()
    earnings = stakingV1.earned(accounts[0])
    assert(earnings[0] > 0)
    assert(earnings[1] > 0)
    assert(earnings[2] == 0)
    assert(earnings[3] == 0)
    assert(earnings[0] >= totalVestingFeesBzrx)
    assert(earnings[1] >= totalVestingFees3Poll)

    # assert False


def testStake_vestingClaimBZRX(requireMainnetFork, stakingV1, bzx, setFeesController, BZRX, vBZRX, iBZRX, accounts, iUSDC, USDC, WETH):

    vBZRX.transfer(accounts[1], 1000*10**18, {'from': vBZRX.address})
    balanceOfvBZRX = vBZRX.balanceOf(accounts[1])
    vBZRX.approve(stakingV1, balanceOfvBZRX, {'from': accounts[1]})
    stakingV1.stake([vBZRX], [balanceOfvBZRX], {'from': accounts[1]})

    # moving time to somewhere 1000 sec after vesting start
    chain.sleep(vBZRX.vestingCliffTimestamp() - chain.time() + 1000)
    chain.mine()

    # BZRX.balanceOf+ vBZRX.balanceOf_bzrx_remaining  should be equal to 1000

    stakingV1.exit({'from': accounts[1]})

    assert(BZRX.balanceOf(accounts[1]) > 0)

    assert True


def testStake_vBZRXVotingRigthsShouldDiminishOverTime(requireMainnetFork, stakingV1, bzx, setFeesController, BZRX, vBZRX, iBZRX, LPT, accounts, iUSDC, USDC, WETH):

    vBZRX.transfer(accounts[1], 100e18, {'from': vBZRX})

    balanceOfvBZRX = vBZRX.balanceOf(accounts[1])

    vBZRX.approve(stakingV1, balanceOfvBZRX, {'from': accounts[1]})

    tokens = [vBZRX]
    amounts = [balanceOfvBZRX]
    tx = stakingV1.stake(tokens, amounts, {'from': accounts[1]})
    votingPower = stakingV1.delegateBalanceOf(accounts[1])
    assert(votingPower <= balanceOfvBZRX/2)

    # moving time to somewhere 1000 sec after vesting start
    chain.sleep(vBZRX.vestingCliffTimestamp() - chain.time() + 1000)
    chain.mine()

    votingPower = stakingV1.delegateBalanceOf(accounts[1])
    assert(votingPower <= balanceOfvBZRX/2)

    # moving time after vesting end
    chain.sleep(vBZRX.vestingEndTimestamp() - chain.time() + 100)
    chain.mine()

    votingPower = stakingV1.delegateBalanceOf(accounts[1])
    assert(votingPower <= balanceOfvBZRX)
    assert True


def testStake_vBZRXVotingRigthsShouldDiminishOverTime2(requireMainnetFork, stakingV1, bzx, setFeesController, BZRX, vBZRX, iBZRX, LPT, accounts, iUSDC, USDC, WETH):

    vBZRX.transfer(accounts[1], 100e18, {'from': vBZRX})

    balanceOfvBZRX = vBZRX.balanceOf(accounts[1])

    vBZRX.approve(stakingV1, balanceOfvBZRX, {'from': accounts[1]})

    tokens = [vBZRX]
    amounts = [balanceOfvBZRX]
    tx = stakingV1.stake(tokens, amounts, {'from': accounts[1]})
    votingPower = stakingV1.delegateBalanceOf(accounts[1])
    assert(votingPower < balanceOfvBZRX/2)

    # moving time to somewhere 1000 sec after vesting start
    chain.sleep(vBZRX.vestingCliffTimestamp() - chain.time() + 1000)
    chain.mine()

    votingPower = stakingV1.delegateBalanceOf(accounts[1])
    assert(votingPower < balanceOfvBZRX/2)

    # moving time after vesting end
    chain.sleep(vBZRX.vestingEndTimestamp() - chain.time() + 100)
    chain.mine()

    votingPower = stakingV1.delegateBalanceOf(accounts[1])
    assert(votingPower < balanceOfvBZRX)
    assert True
