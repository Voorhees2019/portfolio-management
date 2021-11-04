import random

from faker import Faker
from .models import Industry, Technology, Project
from apps.accounts.models import User
from .demo_data import random_industries, random_technologies
from .utils import refresh_elastic_index


fake = Faker()


def generate_fake_field(field_type: str):
    field = {
        'title': fake.catch_phrase,
        'description': fake.text,
        'url': fake.url,
    }
    try:
        return field[field_type]()
    except KeyError:
        return None


def get_or_create_industries(industry_names: list[str] = random_industries):
    industries = []
    for industry in industry_names:
        obj, _ = Industry.objects.get_or_create(title=industry.capitalize())
        industries.append(obj)
    return industries


def get_or_create_technologies(technology_names: list[str] = random_technologies):
    technologies = []
    for technology in technology_names:
        obj, _ = Technology.objects.get_or_create(title=technology.capitalize())
        technologies.append(obj)
    return technologies


def generate_fake_projects(projects_number: int = 10):
    # generate random industries and technologies if not exist
    industries = get_or_create_industries()
    technologies = get_or_create_technologies()

    projects = []
    for _ in range(projects_number):
        try:
            proj = Project.objects.get(
                title=generate_fake_field('title')
            )
        except Project.DoesNotExist:
            proj = Project(
                title=generate_fake_field('title'),
                description=generate_fake_field('description'),
                author=User.objects.first(),
                url=generate_fake_field('url'),
                url_is_active=random.choice([True, False])
            )
            proj.save(refresh_index=False)
        projects.append(proj)
    refresh_elastic_index()

    for project in projects:
        for i in range(random.randint(1, 10)):
            project.industries.add(random.choice(industries))
            project.technologies.add(random.choice(technologies))
