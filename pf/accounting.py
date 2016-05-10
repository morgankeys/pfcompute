"""
accounting.py

Accounting and Financial functions.

project    : pf
version    : 0.0.0
status     : development
modifydate :
createdate :
website    : https://github.com/tmthydvnprt/pf
author     : tmthydvnprt
email      : tim@tmthydvnprt.com
maintainer : tmthydvnprt
license    : MIT
copyright  : Copyright 2016, tmthydvnprt
credits    :

"""

import pandas as import pd

################################################################################################################################
# Financial Statements
################################################################################################################################

def calc_cashflow(transactions=None, category_dict=None):
    """
    Calculate daily cashflow of grouped inflow/outflow based on `category_dict`s from `transactions`, returns a DataFrame.

    Cashflow is split into these sections:
    Inflow
        Operating
            Technical Services
            ...
        Non-Operating
            Interest Income
            Dividend & Capital Gains
            ...
    Outflow
        Operating
            Rent
            Food
            ...
        Non-Operating
            Interest Payments
            ...

    All of the first 3 levels may be user defined by the category dictonary. However the last level must contain a dictionary
    with at least a `category` key and set of categories for the value along with optional parameters.

    ```
    category_dict = 'Inflow': {
        'Operating': {
            # Paychecks
            'Technical Services': {
                'categories': {'Paycheck', ...}, # required set of categories
                'labels': set(),                 # optional set of labels, defaults to set() if not passed in
                'logic': ''                      # optional 'not' string to set inverse of 'labels', defaults to ''
            },
            'User Category': {...}
        },
        'Non-Operating': {
            'User Category': {
                'categories': {...}
            }
        }
    },
    'Outflow': {
        'Operating': {...},
        'Non-Operating': {..}
    }
    ```
    """

    # Add empty 'labels' key to dictionary if they do not have the item
    # Add default 'logic' if it does not exist
    for k0, v0 in category_dict.iteritems():
        for k1, v1 in v0.iteritems():
            for k2, v2 in v1.iteritems():
                if not v2.has_key('labels'):
                    category_dict[k0][k1][k2]['labels'] = set()
                if not v2.has_key('logic'):
                    category_dict[k0][k1][k2]['logic'] = ''

    # Aggregate transactions based on category definition, via 3 level dictionary comprehension
    cashflow_dict = {
        (k0, k1, k2):
            transactions[
                # If it is in the category
                (transactions['category'].isin(v2['categories'])) &
                (
                    # And if is has the correct label
                    (transactions['labels'].apply(
                            lambda x: x.isdisjoint(v2['labels']) if v2['logic'] else not x.isdisjoint(v2['labels'])
                    )) |
                    # Or it does not have any labels
                    (transactions['labels'].apply(lambda x: v2['labels'] == set()))
                )
            ]['amount']

            for k0, v0 in category_dict.iteritems()
                for k1, v1 in v0.iteritems()
                    for k2, v2 in v1.iteritems()
    }

    # Convert to DataFrame
    cols = cashflow_dict.keys()
    cols.sort()
    cashflow = pd.DataFrame([], columns=pd.MultiIndex.from_tuples(cols), index=pd.date_range(transactions.index[-1], transactions.index[0]))
    for cat in cashflow_dict:
        c = pd.DataFrame(cashflow_dict[cat].values, index=cashflow_dict[cat].index, columns=pd.MultiIndex.from_tuples([cat]))
        cashflow[cat] = c.groupby(lambda x: x.date()).sum()

    return cashflow.fillna(0.0)

def cashflow_statement(cashflow=None, period=datetime.datetime.now().year):
    """
    Return a Cashflow Statement for a period from cashflow DataFrame.
    Cashflow will be based on the last entry of account data (e.g. December 31st) for the given `period` time period, which defaults to the current year.  A Net section is automagically calculated.

    Example:
    ```
    cashflow = calc_cashflow(transactions, category_dict=categories)
    cashflowstatement = cashflow_statement(cashflow, period=2015)
    ```
    """

    # Force period to string
    period = str(period)

    # Convert to Statement DataFrame
    cashflow = pd.DataFrame(cashflow_dict, columns=['$'])
    cashflow.index.names = ['Category', 'Type', 'Item']

    # Calculate Net
    net = cashflow[['$']].sum(level=[0,1]).sum(level=1)
    net.index = pd.MultiIndex.from_tuples([('Net', x0, 'Total') for x0 in net.index])
    net.index.names = ['Category', 'Type', 'Item']

    # Add Net
    cashflow = pd.concat([cashflow, net])

    # Calculate percentages of level 0
    cashflow['%'] = 100.0 * cashflow.div(cashflow.sum(level=0), level=0)

    # Calculate heirarchical totals
    l1_totals = cashflow.sum(level=[0,1])
    l1_totals.index = pd.MultiIndex.from_tuples([(x0, x1, 'Total') for x0, x1 in l1_totals.index])
    l1_totals.index.names = ['Category', 'Type', 'Item']

    l0_totals = cashflow.sum(level=[0])
    l0_totals.index = pd.MultiIndex.from_tuples([(x0, 'Total', ' ') for x0 in l0_totals.index])
    l0_totals.index.names = ['Category', 'Type', 'Item']

    # Add totals to dataframe
    cashflow = cashflow.combine_first(l1_totals)
    cashflow = cashflow.combine_first(l0_totals)

    return cashflow
