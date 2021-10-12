import random

from faker import Faker
from .models import Industry, Technology, Project
from django.db import IntegrityError
from apps.accounts.models import User

fake = Faker()


# def bulk_insert(model, fields: list[dict]):
#     # model.objects.bulk_create([model(**entry) for entry in fields], ignore_conflicts=True)
#     objs = [model(**entry) for entry in fields]
#     try:
#         model.objects.bulk_create(objs)
#     except IntegrityError:
#         for obj in objs:
#             try:
#                 obj.save()
#             except IntegrityError:
#                 continue


def generate_fake_field(field_type: str):
    field = {
        'name': fake.catch_phrase,
        'description': fake.text,
        'url': fake.url,
    }
    try:
        return field[field_type]()
    except KeyError:
        return field['name']()


def generate_fake_projects(number: int):
    Project.objects.bulk_create(
        [Project(title=generate_fake_field('name'), description=generate_fake_field('description'),
                 url=generate_fake_field('url'), author=User.objects.get(id=1)) for _ in range(number)])

    projects_ids = list(Project.objects.values_list('id', flat=True))
    industry_ids = list(Industry.objects.values_list('id', flat=True))
    technology_ids = list(Technology.objects.values_list('id', flat=True))

    for industry_id in industry_ids:
        project_to_industry_links = []
        random.shuffle(projects_ids)

        rand_num_projects = random.randint(0, len(projects_ids))
        industry_projects = projects_ids[:rand_num_projects]

        for project_id in industry_projects:
            industry_project = Project.industries.through(project_id=project_id, industry_id=industry_id)
            project_to_industry_links.append(industry_project)
        Project.industries.through.objects.bulk_create(project_to_industry_links, ignore_conflicts=True)

    for technology_id in technology_ids:
        project_to_technology_links = []
        random.shuffle(projects_ids)

        rand_num_projects = random.randint(0, len(projects_ids))
        technology_projects = projects_ids[:rand_num_projects]

        for project_id in technology_projects:
            technology_project = Project.technologies.through(project_id=project_id, technology_id=technology_id)
            project_to_technology_links.append(technology_project)
        Project.technologies.through.objects.bulk_create(project_to_technology_links, ignore_conflicts=True)
