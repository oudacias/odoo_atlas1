# See LICENSE file for full copyright and licensing details.

{
    "name": "Multi-DB Synchronization station",
    "version": "12.0.1.0.0",
    "category": "Tools",
    "license": "AGPL-3",
    "summary": "Multi-DB Synchronization",
    "author": "OpenERP SA, Serpent Consulting Services Pvt. Ltd.",
    "website": "http://www.serpentcs.com",
    "maintainer": "Serpent Consulting Services Pvt. Ltd.",
    "images": [
        "static/description/Synchro.png",
    ],
    "depends": [
        "base",
        "base_synchro",
        'petrol_station_doosys'
    ],
    "data": [
        "views/base_synchro_view.xml",
        "views/petrol_station.xml",
        'views/ir_cron_data.xml',
        "data/data.xml",
        "data/synchro_acount_tax.xml"
    ],
    "installable": True,
}
