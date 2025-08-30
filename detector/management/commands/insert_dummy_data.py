from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from detector.models import Workspace, CropHistory, SoilAnalysis
from django.utils import timezone
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Insert dummy crop history data for testing purposes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username to create dummy data for (default: first user)',
        )
        parser.add_argument(
            '--workspace_id',
            type=int,
            help='Specific workspace ID to insert data into',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=20,
            help='Number of dummy records to create (default: 20)',
        )

    def handle(self, *args, **options):
        username = options['username']
        workspace_id = options.get('workspace_id')
        count = options['count']

        # Get or create a user
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User "{username}" does not exist')
                )
                return
        else:
            user = User.objects.first()
            if not user:
                self.stdout.write(
                    self.style.ERROR('No users exist in the database')
                )
                return

        # Get the specific workspace or first available one
        try:
            if workspace_id:
                workspace = Workspace.objects.get(id=workspace_id, user=user)
                self.stdout.write(
                    self.style.SUCCESS(f'Using specified workspace: {workspace.name} (ID: {workspace.id})')
                )
            else:
                workspace = Workspace.objects.filter(user=user).first()
                if not workspace:
                    workspace = Workspace.objects.create(
                        user=user,
                        name='Test Farm',
                        description='Test workspace for dummy data'
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'Created workspace: {workspace.name}')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'Using existing workspace: {workspace.name}')
                    )
        except Workspace.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Workspace with ID {workspace_id} not found for user {user.username}')
            )
            return
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error with workspace: {e}')
            )
            return

        # Crop names for dummy data
        crops = [
            'rice', 'wheat', 'maize', 'banana', 'apple', 'grapes', 
            'cotton', 'coffee', 'coconut', 'mango', 'orange', 'papaya',
            'chickpea', 'lentil', 'kidneybeans', 'blackgram', 'mungbean',
            'pigeonpeas', 'mothbeans', 'jute', 'muskmelon', 'watermelon',
            'pomegranate'
        ]

        # Generate dummy data
        created_count = 0
        for i in range(count):
            # Generate random soil parameters
            nitrogen = random.uniform(20, 120)
            phosphorus = random.uniform(10, 100)
            potassium = random.uniform(15, 150)
            temperature = random.uniform(15, 35)
            moisture = random.uniform(25, 85)
            ph = random.uniform(5.5, 8.5)
            conductivity = random.uniform(0.5, 3.0)

            # Create soil analysis
            soil_analysis = SoilAnalysis.objects.create(
                user=user,
                workspace=workspace,
                nitrogen=nitrogen,
                phosphorus=phosphorus,
                potassium=potassium,
                temperature=temperature,
                humidity=moisture,
                ph=ph,
                rainfall=random.uniform(20, 200),
                location=f'Field {i+1}',
                notes=f'Dummy soil analysis {i+1}'
            )

            # Create crop history entry
            crop_name = random.choice(crops)
            recommendation_date = timezone.now() - timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )

            CropHistory.objects.create(
                user=user,
                workspace=workspace,
                crop_name=crop_name,
                recommendation_date=recommendation_date,
                soil_analysis=soil_analysis
            )

            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} dummy crop history records '
                f'for user "{user.username}" in workspace "{workspace.name}" (ID: {workspace.id})'
            )
        )

        # Show some statistics
        total_records = CropHistory.objects.filter(user=user, workspace=workspace).count()
        unique_crops = CropHistory.objects.filter(user=user, workspace=workspace).values('crop_name').distinct().count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Total records in workspace: {total_records}'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'Unique crops recommended: {unique_crops}'
            )
        )
