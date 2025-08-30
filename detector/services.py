from django.db import transaction, models
from django.utils import timezone
from .models import SoilAnalysis, CropRecommendation, CropHistory, SystemLog
import numpy as np
import joblib
import os
from tensorflow import keras

class CropRecommendationService:
    """Service class for handling crop recommendation logic"""
    
    def __init__(self):
        self.app_dir = os.path.dirname(__file__)
        self.model_path = os.path.join(self.app_dir, 'ml_models', 'crop_recommendation_model_v3.keras')
        self.scaler_path = os.path.join(self.app_dir, 'ml_models', 'scaler.pkl')
        
        # Load ML model and scaler
        try:
            self.crop_model = keras.models.load_model(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
            self.model_loaded = True
        except Exception as e:
            # Log error loading ML model
            self.model_loaded = False
        
        # Crop labels
        self.crop_labels = [
            'apple', 'banana', 'blackgram', 'chickpea', 'coconut', 'coffee', 'cotton', 'grapes',
            'jute', 'kidneybeans', 'lentil', 'maize', 'mango', 'mothbeans', 'mungbean', 'muskmelon',
            'orange', 'papaya', 'pigeonpeas', 'pomegranate', 'rice', 'watermelon', 'wheat'
        ]
    
    def predict_crop(self, soil_data):
        """
        Predict crop based on soil parameters
        
        Args:
            soil_data (dict): Dictionary containing soil parameters
            
        Returns:
            dict: Prediction results with crop and confidence
        """
        if not self.model_loaded:
            return {
                'error': 'ML model not available',
                'recommended_crop': None,
                'confidence_score': 0.0,
                'alternative_crops': []
            }
        
        try:
            # Extract features in the correct order
            features = np.array([
                soil_data['nitrogen'],
                soil_data['phosphorus'],
                soil_data['potassium'],
                soil_data['temperature'],
                soil_data['humidity'],
                soil_data['ph'],
                soil_data['rainfall']
            ]).reshape(1, -1)
            
            # Scale features
            scaled_features = self.scaler.transform(features)
            
            # Make prediction
            prediction = self.crop_model.predict(scaled_features)
            predicted_class = np.argmax(prediction[0])
            confidence_score = float(prediction[0][predicted_class])
            
            # Get recommended crop
            recommended_crop = self.crop_labels[predicted_class]
            
            # Get alternative crops (top 3 with highest confidence)
            top_indices = np.argsort(prediction[0])[-4:-1][::-1]  # Get top 3 (excluding the top one)
            alternative_crops = [
                {
                    'crop': self.crop_labels[idx],
                    'confidence': float(prediction[0][idx])
                }
                for idx in top_indices
            ]
            
            return {
                'recommended_crop': recommended_crop,
                'confidence_score': confidence_score,
                'alternative_crops': alternative_crops,
                'error': None
            }
            
        except Exception as e:
            return {
                'error': f'Prediction error: {str(e)}',
                'recommended_crop': None,
                'confidence_score': 0.0,
                'alternative_crops': []
            }
    
    def get_crop_recommendations(self, nitrogen, phosphorus, potassium, temperature, moisture, ph, conductivity):
        """
        Get crop recommendations for ESP32 data format
        
        Args:
            nitrogen, phosphorus, potassium: NPK values
            temperature: Temperature in Celsius
            moisture: Moisture content
            ph: pH value
            conductivity: Electrical conductivity
            
        Returns:
            dict: Crop recommendations with top 5 crops
        """
        if not self.model_loaded:
            return {
                'error': 'ML model not available',
                'recommendations': []
            }
        
        try:
            # Convert ESP32 data to model format
            # Map moisture to humidity and set rainfall to 0
            soil_data = {
                'nitrogen': float(nitrogen),
                'phosphorus': float(phosphorus),
                'potassium': float(potassium),
                'temperature': float(temperature),
                'humidity': float(moisture),  # Map moisture to humidity
                'ph': float(ph),
                'rainfall': 0.0  # ESP32 doesn't provide rainfall
            }
            
            # Extract features in the correct order
            features = np.array([
                soil_data['nitrogen'],
                soil_data['phosphorus'],
                soil_data['potassium'],
                soil_data['temperature'],
                soil_data['humidity'],
                soil_data['ph'],
                soil_data['rainfall']
            ]).reshape(1, -1)
            
            # Scale features
            scaled_features = self.scaler.transform(features)
            
            # Make prediction
            prediction = self.crop_model.predict(scaled_features)
            
            # Get top 5 predictions
            top_5_indices = prediction[0].argsort()[-5:][::-1]
            recommendations = [
                {
                    "crop_name": self.crop_labels[idx] if idx < len(self.crop_labels) else str(idx),
                    "probability": float(prediction[0][idx])
                }
                for idx in top_5_indices
            ]
            
            return {
                'error': None,
                'recommendations': recommendations
            }
            
        except Exception as e:
            return {
                'error': f'Prediction error: {str(e)}',
                'recommendations': []
            }
    
    @transaction.atomic
    def create_soil_analysis_and_recommendation(self, user, workspace, soil_params, location=None, notes=None):
        """
        Create soil analysis and crop recommendation in a single transaction
        
        Args:
            user: User object
            workspace: Workspace object
            soil_params (dict): Soil parameters
            location (str): Optional location
            notes (str): Optional notes
            
        Returns:
            tuple: (SoilAnalysis, CropRecommendation) objects
        """
        # Create soil analysis
        soil_analysis = SoilAnalysis.objects.create(
            user=user,
            workspace=workspace,
            nitrogen=soil_params['nitrogen'],
            phosphorus=soil_params['phosphorus'],
            potassium=soil_params['potassium'],
            temperature=soil_params['temperature'],
            humidity=soil_params['humidity'],
            ph=soil_params['ph'],
            rainfall=soil_params['rainfall'],
            location=location,
            notes=notes
        )
        
        # Get crop recommendation
        prediction_result = self.predict_crop(soil_params)
        
        if prediction_result['error']:
            # Log the error
            SystemLog.objects.create(
                log_type='system_error',
                user=user,
                description=f'Crop prediction failed: {prediction_result["error"]}',
                ip_address=None,
                user_agent=None
            )
            return soil_analysis, None
        
        # Create crop recommendation
        crop_recommendation = CropRecommendation.objects.create(
            soil_analysis=soil_analysis,
            recommended_crop=prediction_result['recommended_crop'],
            confidence_score=prediction_result['confidence_score'],
            alternative_crops=prediction_result['alternative_crops']
        )
        
        # Create crop history entry
        CropHistory.objects.create(
            user=user,
            workspace=workspace,
            crop_name=prediction_result['recommended_crop'],
            soil_analysis=soil_analysis
        )
        
        # Log the successful recommendation
        SystemLog.objects.create(
            log_type='crop_recommendation',
            user=user,
            description=f'Crop recommendation created: {prediction_result["recommended_crop"]}',
            ip_address=None,
            user_agent=None
        )
        
        return soil_analysis, crop_recommendation
    
    def get_user_crop_history(self, user, workspace=None, limit=10):
        """
        Get crop recommendation history for a user
        
        Args:
            user: User object
            workspace: Optional workspace filter
            limit: Maximum number of records to return
            
        Returns:
            QuerySet: CropHistory objects
        """
        queryset = CropHistory.objects.filter(user=user)
        
        if workspace:
            queryset = queryset.filter(workspace=workspace)
        
        return queryset[:limit]
    
    def get_workspace_statistics(self, workspace):
        """
        Get statistics for a specific workspace
        
        Args:
            workspace: Workspace object
            
        Returns:
            dict: Statistics data
        """
        analyses = SoilAnalysis.objects.filter(workspace=workspace)
        recommendations = CropRecommendation.objects.filter(soil_analysis__workspace=workspace)
        
        # Get crop distribution
        crop_distribution = {}
        for rec in recommendations:
            crop = rec.recommended_crop
            crop_distribution[crop] = crop_distribution.get(crop, 0) + 1
        
        # Get average confidence scores
        avg_confidence = recommendations.aggregate(
            avg_confidence=models.Avg('confidence_score')
        )['avg_confidence'] or 0
        
        return {
            'total_analyses': analyses.count(),
            'total_recommendations': recommendations.count(),
            'crop_distribution': crop_distribution,
            'average_confidence': round(avg_confidence * 100, 1),
            'last_analysis': analyses.first().analysis_date if analyses.exists() else None
        }

class SoilAnalysisService:
    """Service class for handling soil analysis operations"""
    
    @staticmethod
    def validate_soil_parameters(soil_params):
        """
        Validate soil parameters
        
        Args:
            soil_params (dict): Soil parameters to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        required_fields = ['nitrogen', 'phosphorus', 'potassium', 'temperature', 'humidity', 'ph', 'rainfall']
        
        # Check required fields
        for field in required_fields:
            if field not in soil_params:
                return False, f"Missing required field: {field}"
            
            if soil_params[field] is None:
                return False, f"Field {field} cannot be null"
        
        # Validate ranges
        if not (0 <= soil_params['nitrogen'] <= 140):
            return False, "Nitrogen must be between 0 and 140 kg/ha"
        
        if not (5 <= soil_params['phosphorus'] <= 145):
            return False, "Phosphorus must be between 5 and 145 kg/ha"
        
        if not (5 <= soil_params['potassium'] <= 205):
            return False, "Potassium must be between 5 and 205 kg/ha"
        
        if not (8.5 <= soil_params['temperature'] <= 43.7):
            return False, "Temperature must be between 8.5 and 43.7°C"
        
        if not (14.3 <= soil_params['humidity'] <= 99.9):
            return False, "Humidity must be between 14.3 and 99.9%"
        
        if not (3.5 <= soil_params['ph'] <= 10):
            return False, "pH must be between 3.5 and 10"
        
        if not (20.2 <= soil_params['rainfall'] <= 298.6):
            return False, "Rainfall must be between 20.2 and 298.6 mm"
        
        return True, None
    
    @staticmethod
    def get_soil_analysis_summary(user, workspace=None):
        """
        Get summary of soil analyses for a user
        
        Args:
            user: User object
            workspace: Optional workspace filter
            
        Returns:
            dict: Summary data
        """
        queryset = SoilAnalysis.objects.filter(user=user)
        
        if workspace:
            queryset = queryset.filter(workspace=workspace)
        
        if not queryset.exists():
            return {
                'total_analyses': 0,
                'average_nitrogen': 0,
                'average_phosphorus': 0,
                'average_potassium': 0,
                'average_ph': 0,
                'last_analysis': None
            }
        
        # Calculate averages
        summary = queryset.aggregate(
            total_analyses=models.Count('id'),
            average_nitrogen=models.Avg('nitrogen'),
            average_phosphorus=models.Avg('phosphorus'),
            average_potassium=models.Avg('potassium'),
            average_ph=models.Avg('ph')
        )
        
        summary['last_analysis'] = queryset.latest('analysis_date').analysis_date
        
        # Round averages
        for key in ['average_nitrogen', 'average_phosphorus', 'average_potassium', 'average_ph']:
            if summary[key]:
                summary[key] = round(summary[key], 2)
        
        return summary
    
    @staticmethod
    def analyze_soil(nitrogen, phosphorus, potassium, temperature, moisture, ph, conductivity):
        """
        Analyze soil parameters and provide insights
        
        Args:
            nitrogen, phosphorus, potassium: NPK values
            temperature: Temperature in Celsius
            moisture: Moisture content
            ph: pH value
            conductivity: Electrical conductivity
            
        Returns:
            dict: Soil analysis results
        """
        try:
            # Convert to float for calculations
            nitrogen = float(nitrogen)
            phosphorus = float(phosphorus)
            potassium = float(potassium)
            temperature = float(temperature)
            moisture = float(moisture)
            ph = float(ph)
            conductivity = float(conductivity)
            
            # Analyze NPK levels
            npk_analysis = {
                'nitrogen': {
                    'value': nitrogen,
                    'status': 'Low' if nitrogen < 50 else 'Medium' if nitrogen < 100 else 'High',
                    'recommendation': 'Consider nitrogen fertilization' if nitrogen < 50 else 'Nitrogen levels are adequate'
                },
                'phosphorus': {
                    'value': phosphorus,
                    'status': 'Low' if phosphorus < 25 else 'Medium' if phosphorus < 75 else 'High',
                    'recommendation': 'Consider phosphorus fertilization' if phosphorus < 25 else 'Phosphorus levels are adequate'
                },
                'potassium': {
                    'value': potassium,
                    'status': 'Low' if potassium < 50 else 'Medium' if potassium < 150 else 'High',
                    'recommendation': 'Consider potassium fertilization' if potassium < 50 else 'Potassium levels are adequate'
                }
            }
            
            # Analyze pH
            ph_analysis = {
                'value': ph,
                'status': 'Acidic' if ph < 6.5 else 'Neutral' if ph < 7.5 else 'Alkaline',
                'recommendation': 'Consider lime application' if ph < 6.0 else 'pH is suitable for most crops' if 6.0 <= ph <= 7.5 else 'Consider sulfur application'
            }
            
            # Analyze temperature
            temp_analysis = {
                'value': temperature,
                'status': 'Cold' if temperature < 15 else 'Moderate' if temperature < 25 else 'Hot',
                'recommendation': 'Suitable for cool-season crops' if temperature < 15 else 'Suitable for most crops' if 15 <= temperature <= 30 else 'Consider heat-tolerant crops'
            }
            
            # Analyze moisture
            moisture_analysis = {
                'value': moisture,
                'status': 'Low' if moisture < 30 else 'Moderate' if moisture < 70 else 'High',
                'recommendation': 'Consider irrigation' if moisture < 30 else 'Moisture levels are adequate' if 30 <= moisture <= 70 else 'Consider drainage'
            }
            
            # Overall soil health score (0-100)
            health_score = 0
            
            # NPK contribution (40 points)
            if npk_analysis['nitrogen']['status'] == 'Medium' or npk_analysis['nitrogen']['status'] == 'High':
                health_score += 15
            elif npk_analysis['nitrogen']['status'] == 'Low':
                health_score += 5
                
            if npk_analysis['phosphorus']['status'] == 'Medium' or npk_analysis['phosphorus']['status'] == 'High':
                health_score += 15
            elif npk_analysis['phosphorus']['status'] == 'Low':
                health_score += 5
                
            if npk_analysis['potassium']['status'] == 'Medium' or npk_analysis['potassium']['status'] == 'High':
                health_score += 10
            elif npk_analysis['potassium']['status'] == 'Low':
                health_score += 3
            
            # pH contribution (20 points)
            if 6.0 <= ph <= 7.5:
                health_score += 20
            elif 5.5 <= ph <= 8.0:
                health_score += 15
            else:
                health_score += 5
            
            # Temperature contribution (20 points)
            if 15 <= temperature <= 30:
                health_score += 20
            elif 10 <= temperature <= 35:
                health_score += 15
            else:
                health_score += 10
            
            # Moisture contribution (20 points)
            if 30 <= moisture <= 70:
                health_score += 20
            elif 20 <= moisture <= 80:
                health_score += 15
            else:
                health_score += 10
            
            return {
                'npk_analysis': npk_analysis,
                'ph_analysis': ph_analysis,
                'temperature_analysis': temp_analysis,
                'moisture_analysis': moisture_analysis,
                'conductivity': conductivity,
                'overall_health_score': min(100, health_score),
                'health_status': 'Excellent' if health_score >= 80 else 'Good' if health_score >= 60 else 'Fair' if health_score >= 40 else 'Poor'
            }
            
        except Exception as e:
            return {
                'error': f'Soil analysis error: {str(e)}',
                'npk_analysis': {},
                'ph_analysis': {},
                'temperature_analysis': {},
                'moisture_analysis': {},
                'conductivity': 0,
                'overall_health_score': 0,
                'health_status': 'Error'
            }
    
    @staticmethod
    def get_user_soil_analyses(user, workspace=None, limit=100):
        """
        Get soil analyses for a user
        
        Args:
            user: User object
            workspace: Optional workspace filter
            limit: Maximum number of records to return
            
        Returns:
            QuerySet: SoilAnalysis objects
        """
        queryset = SoilAnalysis.objects.filter(user=user)
        
        if workspace:
            queryset = queryset.filter(workspace=workspace)
        
        return queryset.order_by('-analysis_date')[:limit]
