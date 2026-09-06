import os
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from azure.identity import DefaultAzureCredential
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.costmanagement.models import QueryDefinition, QueryTimePeriod, QueryDataset, QueryAggregation

def fetch_cost_data(subscription_id: str, days: int = 30, cache_file: Path = Path("cost_data.csv")) -> pd.DataFrame:
    """
    Fetches daily cost data for a given subscription over the last `days` days.
    Caches the result to a CSV file.
    """
    if not subscription_id or subscription_id == "your-subscription-id":
        raise ValueError("A valid Azure Subscription ID must be provided to fetch data.")
        
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    credential = DefaultAzureCredential()
    client = CostManagementClient(credential)
    
    scope = f"/subscriptions/{subscription_id}"
    
    query = QueryDefinition(
        type="Usage",
        timeframe="Custom",
        time_period=QueryTimePeriod(
            from_property=start_date,
            to=end_date
        ),
        dataset=QueryDataset(
            granularity="Daily",
            aggregation={
                "totalCost": QueryAggregation(name="PreTaxCost", function="Sum")
            }
        )
    )
    
    response = client.query.usage(scope, query)
    
    if not response.rows:
        df = pd.DataFrame(columns=["date", "cost"])
    else:
        records = []
        for row in response.rows:
            cost = float(row[0])
            date_int = row[1]
            date_val = pd.to_datetime(str(date_int), format="%Y%m%d")
            records.append({"date": date_val, "cost": cost})
            
        df = pd.DataFrame(records)
        df.sort_values("date", inplace=True)
        df.reset_index(drop=True, inplace=True)
        
    df.to_csv(cache_file, index=False)
    return df
