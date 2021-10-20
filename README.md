# discord-gas-bot
Get the ethereum gas prices in your own discord server.

The gas price reflected here is in Gwei, you can either run it as command with `!gas` or it will show up the price in the sidebar.

## Dependencies
Install all dependencies:
```
pip install -r requirements.txt
```

### Gas Price Bot
1. Copy the [template config](config.yaml.tmpl) and configure with API keys.
```
cp config.yaml.tmpl config.yaml
```
Change config.yaml with the Discord bot key and Etherscan, EthGasStation, or Gasnow API keys.

2. Run a gas price bot using Etherscan API:
```
python gas_bot.py -s ethgasstation
```
Replace `etherscan` with `gasnow` to use Gasnow API (no key required!) or `ethgasstation` to use EthGasStation API.

Ethgasstation is the recommended source

# additional features
This fork contains the addition of the `!alert` command. The command accepts two arguments the first one is whether you want to be notified when gas is either `above` or `below` a specified number. The second command is the gas price you want to be notified for.

Examples:

`!alert below 50` would tell the bot to dm you when gas is below 50
`!alert above 100` would tell the bot to dm you when gas is above 100
