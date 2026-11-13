from django.db import migrations


SERVICES = [
    ("Screen replacement", "Cracked, blank or unresponsive display inspection and repair."),
    ("Battery replacement", "Battery health, charging and replacement assessment."),
    ("Charging port repair", "Charging port inspection, cleaning and repair assessment."),
    ("Camera repair", "Front or rear camera inspection and repair assessment."),
    ("Speaker and microphone repair", "Audio input and output troubleshooting."),
    ("Water damage repair", "Device inspection after liquid exposure; repairability is assessed first."),
    ("Motherboard repair", "Board-level fault assessment by a technician."),
    ("Software troubleshooting", "Help with software faults, setup and device recovery."),
    ("Operating system installation and updates", "Operating system installation or update support."),
]


def add_services(apps, schema_editor):
    Service = apps.get_model("esite", "RepairService")
    for order, (name, description) in enumerate(SERVICES):
        slug = name.lower().replace(" and ", "-").replace(" ", "-")
        Service.objects.get_or_create(
            slug=slug,
            defaults={"name": name, "description": description, "display_order": order},
        )


def remove_services(apps, schema_editor):
    Service = apps.get_model("esite", "RepairService")
    Service.objects.filter(slug__in=[
        name.lower().replace(" and ", "-").replace(" ", "-") for name, _ in SERVICES
    ]).delete()


class Migration(migrations.Migration):
    dependencies = [("esite", "0004_promotion_repairinvoice_repairservice_testimonial_and_more")]
    operations = [migrations.RunPython(add_services, remove_services)]
