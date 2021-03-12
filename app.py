from flask import Flask, render_template, redirect, url_for, send_file, request
from submit import SubmitURL
import requests

from data import connect_to_presto, pp_sjson_comparison

app = Flask(__name__)

# Using a production configuration
# app.config.from_object("config.ProdConfig")

# Using a development configuration
app.config.from_object("config.DevConfig")


@app.route("/", methods=["GET", "POST"])
def get_data():

    form = SubmitURL()
    sellers = {}
    data = {}
    matched = "populated once data is processed"

    if form.validate():
        url = form.sellers_json_url.data

        r = requests.get(url)
        if r.status_code == 200:
            data = r.json()
            sellers = data.get("sellers")
        else:
            print(f"ERROR: {r.status_code}, {r.reason}")

        """ running data analysis on seller.json from data.py """
        try:
            connect_to_presto()
            matched = pp_sjson_comparison(data)
        except KeyError as err:
            print(err)

    """ get contact details """
    contact_data = {
        "email": data.get("contact_email"),
        "address": data.get("contact_address"),
        "version": data.get("version"),
    }

    """ remove duplicates from seller['domain'] """
    unique = {each["domain"]: each for each in sellers}.values()

    """ get count for valid domains """
    valid_domain_count = 0
    non_valid_domain_count = 0

    for vdc in unique:
        if vdc.get("domain", "domain_missing") != "domain_missing":
            valid_domain_count += 1
        else:
            non_valid_domain_count += 1

    """ get count for "PUBLISHER """
    publisher_count = 0
    for publisher in unique:
        if (
            publisher["seller_type"].lower() == "publisher"
            and publisher.get("domain", "domain_missing") != "domain_missing"
        ):
            publisher_count += 1

    """ get count for "INTERMEDIARY """
    intermediary_count = 0
    for intermediary in unique:
        if (
            intermediary["seller_type"].lower() == "intermediary"
            and intermediary.get("domain", "domain_missing") != "domain_missing"
        ):
            intermediary_count += 1

    """ get count for "BOTH" """
    both_count = 0
    for both in unique:
        if (
            both["seller_type"].lower() == "both"
            and both.get("domain", "domain_missing") != "domain_missing"
        ):
            both_count += 1

    total_entries = valid_domain_count + non_valid_domain_count

    try:
        pub_pct = int(100 * publisher_count / valid_domain_count)
    except ZeroDivisionError as err:
        pub_pct = 0

    return render_template(
        "home.html",
        contact_info=contact_data,
        publisher=publisher_count,
        intermediary=intermediary_count,
        both_count=both_count,
        vdc=valid_domain_count,
        nvdc=non_valid_domain_count,
        total_entries=total_entries,
        form=form,
        matched_enteries=matched,
        pub_pct=pub_pct,
    )


""" download sellerjson_output.csv via Download Btn """


@app.route("/download/")
def download_file():
    app.logger.debug(f"This endpoint is: {request.endpoint}")
    return send_file("./files/sellerjson_output.csv", as_attachment=True)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)