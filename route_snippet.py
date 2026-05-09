# In mineral_app.py — diese zwei Zeilen am Ende ergänzen:

from mineral_app.faq.prospektivitaet import faq_prospektivitaet_page

app.add_page(
    faq_prospektivitaet_page,
    route="/faq/prospektivitaet",
    title="EMI ExploreIQ · Hilfe Prospektivität",
)
