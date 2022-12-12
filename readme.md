# Experimental Economics with otree

This project tries experimental economics with [otree](https://github.com/oTree-org/oTree), a python
library for behavioral research.

Until now the only app is an Experimental Auction Market as described in Smith (1965). 
It tests the efficiency of markets and the ability of participants to predict the market price under the condition of excess sellers.


## oTree How-To

### Installation

```bash
pwd
python3 -m venv venv
source venv/bin/activate
pip3 install otree
which otree
otree
```

### neues Projekt + neue App

```bash
otree startproject meinprojekt
cd meinprojekt
otree startapp
```

### Start des Servers

```bash
otree devserver
```

Ergebnis: 

```
Open your browser to http://localhost:8000/
To quit the server, press Control+C.
```

