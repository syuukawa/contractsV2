
### flattener

cd flattenerV2/contracts

truffle-flattener  contracts/testhelpers/TestToken.sol > flattener/TestToken.sol

truffle-flattener  contracts/connectors/loantoken/LoanTokenSettings.sol > flattener/LoanTokenSettings.sol

### run scripts

export WEB3_INFURA_PROJECT_ID='a0dde221820e46fab7be679df395444d'

brownie run deploy_protocol.py --network kovan

brownie run scripts/add-token/add-itoken.py --network kovan

https://github.com/syuukawa/contractsV2
