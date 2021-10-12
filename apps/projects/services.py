import csv
import os
import random

from faker import Faker
from .models import Industry, Technology, Project
from apps.accounts.models import User
from .industry_list import random_industries
from .technology_list import random_technologies
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


def generate_fake_projects(number: int):
    Project.objects.bulk_create(
        [Project(title=generate_fake_field('title'), description=generate_fake_field('description'),
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


def generate_projects_csv(projects_num: int = 30):
    filename = 'projects.csv'
    # Delete existing random projects csv file
    if os.path.exists(filename):
        os.remove(filename)

    d = {
        'technologies': random_industries,
        'industries': random_technologies,
    }

    with open('projects.csv', mode='w') as file:
        writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        headers = ['title', 'url', 'technologies', 'description', 'industries', 'notes']
        # write headers
        writer.writerow(headers)

        # write fake data
        for row_num in range(projects_num):
            row = []
            for col in headers:
                fake_field = generate_fake_field(col)
                if fake_field:
                    row.append(fake_field)
                else:
                    # add random notes
                    if col == 'notes':
                        if random.random() <= 0.5:
                            row.append('Doesn\'t work')
                        continue
                    # add random technologies and industries
                    cell_value = []
                    for i in range(random.randint(0, 10)):
                        random_title = random.choice(d[col])
                        if random_title in cell_value:
                            continue
                        cell_value.append(random_title)
                    cell_value = ', '.join(cell_value)
                    row.append(cell_value)
            writer.writerow(row)
