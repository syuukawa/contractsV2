#!/usr/bin/python3

from brownie import *
from brownie import network, accounts
from brownie.network.contract import InterfaceContainer
from brownie.network.state import _add_contract, _remove_contract
from brownie.network.contract import Contract
import time
import pdb

def main():
    deployAddItoken()

def deployAddItoken():
    global acct
    acct = accounts.load('testnet_admin')
    print("Loaded account",acct)

    #acct = accounts.at("0x2592C903BE5d797e5411e046c2435826A0F8e054", force=True)
    underlyingSymbol = "WOO"
    iTokenSymbol = "i{}".format(underlyingSymbol)
    iTokenName = "Fulcrum {} iToken ({})".format(underlyingSymbol, iTokenSymbol)  


    loanTokenAddress = acct.deploy(TestToken, underlyingSymbol, underlyingSymbol, 18, 1e50).address  
        # TestToken 0x3bddd76deaa06d40edb821a8a82f90ea227a29e7

    # loanTokenLogicStandard = "0xfb772316a54dcd439964b561fc2c173697aeeb5b" # logic of the LoanToken
    loanTokenLogicStandard = acct.deploy(LoanTokenLogicStandard, acct).address
        # loanTokenLogicStandard 0x9d2a4b4aef7d49523e8e0cdc9a2bd3f6264a38d3

    # TODO insert real price feed below (usdc now)
    # priceFeedAddress = "0xA9F9F897dD367C416e350c33a92fC12e53e1Cee5"
    # bzxAddress = "0xD8Ee69652E4e4838f2531732a46d1f7F584F0b7f"
    priceFeedAddress = "0x9326c5920d4B5D4cd8Fd1a0a3e5358C40B8b93b8"
    bzxAddress = "0x8809CFF451f673Bd47efc975A53b2e29dd4D84f3"

    ##?????????????
    #https://etherscan.io/address/0xf0E474592B455579Fe580D610b846BdBb529C6F7#code
    # 1.TokenRegistry合约单独部署 0x42cea676068a409f13dfe7d9fcc00817b343d929
    bzxRegistry = Contract.from_abi("bzxRegistry", address="0x42cea676068a409f13dfe7d9fcc00817b343d929", abi=TokenRegistry.abi)


    # Deployment

    iTokenProxy = acct.deploy(LoanToken, acct, loanTokenLogicStandard)
    # LoanToken 0xea5361251b2a784590b843118d728cd4f1a9e65f

    loanTokenSettings = acct.deploy(LoanTokenSettings)
    # loanTokenSettings 0xf3efb19f4109c0376b8e362e6192fbfe13b208f7
    calldata = loanTokenSettings.initialize.encode_input(
        loanTokenAddress, iTokenName, iTokenSymbol)


    iToken = Contract.from_abi("loanTokenLogicStandard",
                            iTokenProxy, LoanTokenLogicStandard.abi, acct)
    iToken.updateSettings(loanTokenSettings, calldata)


    # Setting price Feed
    bzx = Contract.from_abi("bzx", address=bzxAddress, abi=interface.IBZx.abi, owner=acct)
    priceFeed = Contract.from_abi("pricefeed", bzx.priceFeeds(), abi=PriceFeeds.abi, owner=acct)
    priceFeed.setPriceFeed([loanTokenAddress], [priceFeedAddress], {'from': acct})


    bzx.setLoanPool([iToken], [loanTokenAddress])
    bzx.setSupportedTokens([loanTokenAddress], [True])


    # Setting margin settings


    loanTokenSettingsLowerAdmin = acct.deploy(
        LoanTokenSettingsLowerAdmin)  # TODO use Tom address


    # iTokenLoanTokenSettingsLowerAdmin = Contract.from_abi(
    #     "loanToken", address="0xcd273a029fB6aaa89ca9A7101C5901b1f429d457", abi=LoanTokenSettingsLowerAdmin.abi, owner=acct)
    # loanToken https://kovan.etherscan.io/address/0x94aef76babbc856fc91b94b2cae5d40ce154ff03
    # 0x94Aef76babBC856fC91b94b2caE5D40CE154ff03
    base_data = [
        b"0x0",  # id
        False,  # active
        str(acct),  # owner
        "0x0000000000000000000000000000000000000001",  # loanToken
        "0x0000000000000000000000000000000000000002",  # collateralToken
        Wei("20 ether"),  # minInitialMargin
        Wei("15 ether"),  # maintenanceMargin
        0  # fixedLoanTerm
    ]

    params = []
    

    supportedTokenAssetsPairs = bzxRegistry.getTokens(0, 100) # TODO move this into a loop for permissionless to support more than 100
    loanTokensArr = []
    collateralTokensArr = []
    amountsArr =[]

    for tokenAssetPair in supportedTokenAssetsPairs:
        if tokenAssetPair[0] == iToken.address:
            continue
        # below is to allow different collateral for new iToken
        base_data_copy = base_data.copy()
        base_data_copy[3] = loanTokenAddress
        base_data_copy[4] = tokenAssetPair[1] # pair is iToken, Underlying
        print(base_data_copy)
        params.append(base_data_copy)
        
        loanTokensArr.append(loanTokenAddress)
        collateralTokensArr.append(tokenAssetPair[1])
        amountsArr.append(7*10**18)


    calldata = loanTokenSettingsLowerAdmin.setupLoanParams.encode_input(params, True)
    iToken.updateSettings(loanTokenSettingsLowerAdmin.address, calldata, {"from": acct})

    calldata = loanTokenSettingsLowerAdmin.setupLoanParams.encode_input(params, False)
    iToken.updateSettings(loanTokenSettingsLowerAdmin.address, calldata, {"from": acct})


    params.clear()
    for tokenAssetPair in supportedTokenAssetsPairs:
        # below is to allow new iToken.loanTokenAddress in other existing iTokens
        existingIToken = Contract.from_abi("existingIToken", address=tokenAssetPair[0], abi=LoanTokenLogicStandard.abi, owner=acct)
        
        base_data_copy = base_data.copy()
        existingITokenLoanTokenAddress = existingIToken.loanTokenAddress()
        base_data_copy[3] = existingITokenLoanTokenAddress
        base_data_copy[4] = loanTokenAddress # pair is iToken, Underlying
        print(base_data_copy)
        params.append(base_data_copy)


        #calldata = loanTokenSettingsLowerAdmin.setupLoanParams.encode_input(params, True)
        #existingIToken.updateSettings(loanTokenSettingsLowerAdmin.address, calldata, {"from": acct})

        # ?????????????
        # calldata = loanTokenSettingsLowerAdmin.setupLoanParams.encode_input(params, False)
        # existingIToken.updateSettings(loanTokenSettingsLowerAdmin.address, calldata, {"from": acct})

        loanTokensArr.append(loanTokenAddress)
        collateralTokensArr.append(existingITokenLoanTokenAddress)
        amountsArr.append(7*10**18)
        params.clear()


    # Set demand curve
    calldata = loanTokenSettingsLowerAdmin.setDemandCurve.encode_input(0, 23.75*10**18, 0, 0, 80*10**18, 80*10**18, 120*10**18)
    iToken.updateSettings(loanTokenSettingsLowerAdmin.address, calldata, {"from": acct})


    bzx.setLiquidationIncentivePercent(loanTokensArr, collateralTokensArr, amountsArr)

    # main()
