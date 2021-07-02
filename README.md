# Welcome to Koi

## Configuration


### Brokerage Setup

#### Robinhood
For RH support create a file named `config.ini` located inside the top level `config` folder. Format it as so:
```
[main]
regular_account = [Account ID]
regular_username = [Username]
paper_account = [Account ID]
paper_username = [Username]
```



### Other Env Options
`PHONE`: Optionally add a phone number to be notified of transactions (Mac + iMessage Only)


## Running
To start Koi after you have your desired configuration and have installed the required npm/pip packages, simply run

```
python3 app.py
```

in your terminal.

