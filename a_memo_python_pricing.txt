# Documentation du Code - Pricing d'Options

## Structure du Programme

### 1. Main.py - Point d'entrée principal


#### Paramètres d'Entrée :

1. Option (`Opt` class) :
```python
option_data = Opt(
    strike=101,                    # Prix d'exercice
    maturity_date='2024-12-26',    # Date de maturité (format: 'YYYY-MM-DD')
    is_american=False,             # Type américain (True/False)
    is_call=True                   # Call (True) ou Put (False)
)
```

2. Marché (`Mk` class) :
```python
market_data = Mk(
    interest_rate=0.06,            # Taux d'intérêt (6%)
    volatility=0.21,               # Volatilité (21%)
    dividend=3,                    # Montant du dividende
    start_price=100,               # Prix spot initial
    start_date='2024-03-01',       # Date de début
    div_date='2024-06-02'         # Date de versement du dividende
)
```

3. Paramètres de l'Arbre :
- `nb_steps` : Nombre de pas dans l'arbre (par défaut: 100)
- `delta_t` : Calculé automatiquement comme time_to_maturity / nb_steps

### 2. Processus d'Exécution

1. Initialisation :
   - Création de l'instance Option
   - Création de l'instance Market
   - Calcul du temps jusqu'à maturité
   - Configuration de l'arbre

2. Construction de l'arbre :
   - Utilisation de la classe Tree
   - Construction récursive des nœuds

3. Pricing :
   - Utilisation de la classe Pricer
   - Calcul du prix de l'option

### 3. Fichiers de Visualisation

Tous les graphiques utilisent les instances `option_data` et `market_data` du main :

#### graph_probability.py
- Analyse la distribution des prix à maturité
- Utilisation : `python graph_probability.py`

#### graph_price.py
- Montre l'évolution du prix
- Utilisation : `python graph_price.py`

#### graph_greeks.py
- Calcule et affiche Delta, Gamma, Theta, Vega
- Utilisation : `python graph_greeks.py`

#### graph_convergence_BS.py
- Compare avec Black-Scholes
- Utilisation : `python graph_convergence_BS.py`

## Notes Importantes

1. Gestion des Dates :
   - Format requis : 'YYYY-MM-DD'
   - Vérifier que div_date est entre start_date et maturity_date

2. Dividendes :
   - Montant en valeur absolue
   - Impact sur la construction de l'arbre

3. Performance :
   - Le programme affiche les temps d'exécution pour :
     * Construction de l'arbre
     * Pricing
     * Temps total
   - Note sur le cache : Le cache n'est pas vidé pour permettre la création des plots

## Exemples d'Utilisation

### Exemple Standard
```python
# Option européenne standard
option_data = Opt(
    strike=100,
    maturity_date='2024-12-31',
    is_american=False,
    is_call=True
)

market_data = Mk(
    interest_rate=0.05,
    volatility=0.2,
    dividend=0,
    start_price=100,
    start_date='2024-01-01',
    div_date='2024-06-30'
)

nb_steps = 100
```

### Option Américaine avec Dividende
```python
option_data = Opt(
    strike=101,
    maturity_date='2024-12-26',
    is_american=True,
    is_call=False  # Put américain
)

market_data = Mk(
    interest_rate=0.06,
    volatility=0.21,
    dividend=3,
    start_price=100,
    start_date='2024-03-01',
    div_date='2024-06-02'
)
```

## Erreurs Communes

1. Erreurs de Date :
   - Vérifier le format 'YYYY-MM-DD'
   - S'assurer de la cohérence chronologique

2. Erreurs de Dividende :
   - Vérifier que div_date est cohérente
   - Dividend doit être positif ou nul
