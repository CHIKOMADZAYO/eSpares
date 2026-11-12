from django.db import migrations


BRAND_NAMES = (
    "Dell",
    "HP",
    "Lenovo",
    "Samsung",
    "Apple",
    "TECNO",
    "Infinix",
    "OPPO",
    "vivo",
    "realme",
)


def seed_brands(apps, schema_editor):
    Brand = apps.get_model("esite", "Brand")
    for name in BRAND_NAMES:
        Brand.objects.get_or_create(name=name)


class Migration(migrations.Migration):
    dependencies = [
        ("esite", "0002_brand_product_brand"),
    ]

    operations = [
        migrations.RunPython(seed_brands, migrations.RunPython.noop),
    ]
