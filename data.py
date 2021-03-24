import prestodb
import pandas as pd
import config

c = config.Config()


def connect_to_presto():
    with prestodb.dbapi.connect(
        host=c.DBHOST,
        port=int(c.DBPORT),
        user=c.DBUSER,
        catalog="gridhive",
        schema="rpt",
        http_scheme="https",
        auth=prestodb.auth.BasicAuthentication(c.DBUSER, c.DBPWD),
    ) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            select rootdomain, sum(revcpm*impressions/1000) as revenue
            from rpt.rptdaily where date(day) >= date(date_sub(current_date,1)) and date(day) < current_date group by 1
            having sum(revcpm*impressions/1000) > 100
            """
        )
        rows = cur.fetchall()
        return rows


def pp_sjson_comparison(data):
    rpt_data = connect_to_presto()
    df_rpt = pd.DataFrame(rpt_data, columns=["domain", "revenue"])

    """ adding sellers.json seller {} into a panads df """
    sj_data = data
    df_sj = pd.json_normalize(sj_data, record_path="sellers", errors="ignore")

    """ merging both dataframes & removing duplicates """
    df_merged = df_rpt.merge(df_sj, how="inner", on="domain", indicator=True)
    df_merged_no_dupes = df_merged.drop_duplicates(subset=["domain"]).reset_index(
        drop=True
    )

    """ counting rows no dataframe with no dupes """
    i = df_merged_no_dupes.index
    matched_domains = len(i) - 1
    revenue = round(df_merged_no_dupes["revenue"].sum(), 2)

    """ store matched data into a file """
    merged_df_rpt = df_rpt.merge(df_sj, how="right", on="domain", indicator=True)
    merged_df_rpt.to_csv(f"./files/sellerjson_output.csv")

    return f"We saw {matched_domains} matched domains, which generated ${revenue:,.0f} in revenue in the past 24hrs"
