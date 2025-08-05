#!/usr/bin/env python3
"""
Vedic Astrology Prediction Generator
Advanced system for generating personalized horoscope readings based on birth details
"""

import ephem
import pytz
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import math

@dataclass
class BirthDetails:
    """Store birth information"""
    name: str
    birth_date: datetime
    birth_time: str
    birth_place: str
    latitude: float
    longitude: float
    timezone: str

class VedicAstrology:
    """Main class for Vedic astrology calculations and predictions"""
    
    # Zodiac signs in Vedic astrology
    SIGNS = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    
    # Nakshatras (lunar mansions)
    NAKSHATRAS = [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashirsha", "Ardra",
        "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
        "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
        "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
        "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
    ]
    
    # Dasha periods (years)
    DASHA_PERIODS = {
        "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
        "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17
    }
    
    def __init__(self):
        self.birth_chart = {}
        self.current_dasha = {}
        self.predictions = {}
    
    def calculate_planetary_positions(self, birth_details: BirthDetails) -> Dict:
        """Calculate planetary positions for the birth chart"""
        
        # Convert to UTC for calculations
        birth_dt = birth_details.birth_date
        
        # Create observer location
        observer = ephem.Observer()
        observer.lat = str(birth_details.latitude)
        observer.lon = str(birth_details.longitude) 
        observer.date = birth_dt
        
        planets = {}
        
        # Calculate positions for all planets
        sun = ephem.Sun(observer)
        moon = ephem.Moon(observer)
        mercury = ephem.Mercury(observer)
        venus = ephem.Venus(observer)
        mars = ephem.Mars(observer)
        jupiter = ephem.Jupiter(observer)
        saturn = ephem.Saturn(observer)
        
        # Convert to tropical longitude and then to sidereal (subtract ayanamsa)
        ayanamsa = self.calculate_ayanamsa(birth_dt)
        
        # Use ecliptic longitude instead of RA
        planets['Sun'] = self.get_sign_and_degree(float(sun.hlong) * 180/math.pi - ayanamsa)
        planets['Moon'] = self.get_sign_and_degree(float(moon.hlong) * 180/math.pi - ayanamsa)
        planets['Mercury'] = self.get_sign_and_degree(float(mercury.hlong) * 180/math.pi - ayanamsa)
        planets['Venus'] = self.get_sign_and_degree(float(venus.hlong) * 180/math.pi - ayanamsa)
        planets['Mars'] = self.get_sign_and_degree(float(mars.hlong) * 180/math.pi - ayanamsa)
        planets['Jupiter'] = self.get_sign_and_degree(float(jupiter.hlong) * 180/math.pi - ayanamsa)
        planets['Saturn'] = self.get_sign_and_degree(float(saturn.hlong) * 180/math.pi - ayanamsa)
        
        # Calculate Rahu and Ketu (lunar nodes)
        moon_node = self.calculate_lunar_nodes(birth_dt)
        planets['Rahu'] = self.get_sign_and_degree(moon_node['rahu'])
        planets['Ketu'] = self.get_sign_and_degree(moon_node['ketu'])
        
        return planets
    
    def calculate_ayanamsa(self, date: datetime) -> float:
        """Calculate ayanamsa (precession correction) for sidereal calculations"""
        # Using Lahiri ayanamsa approximation
        year = date.year + (date.month - 1) / 12.0 + (date.day - 1) / 365.25
        ayanamsa = 23.85 + (year - 1900) * 0.013888889
        return ayanamsa
    
    def calculate_lunar_nodes(self, date: datetime) -> Dict:
        """Calculate Rahu and Ketu positions"""
        # Simplified calculation - in practice, use more precise ephemeris
        days_since_epoch = (date - datetime(1900, 1, 1)).days
        mean_node = 125.044522 - 0.0529539222 * days_since_epoch
        
        rahu = mean_node % 360
        ketu = (rahu + 180) % 360
        
        return {'rahu': rahu, 'ketu': ketu}
    
    def get_sign_and_degree(self, longitude: float) -> Dict:
        """Convert longitude to sign and degree"""
        longitude = longitude % 360
        sign_num = int(longitude // 30)
        degree = longitude % 30
        
        return {
            'sign': self.SIGNS[sign_num],
            'degree': degree,
            'sign_num': sign_num
        }
    
    def calculate_ascendant(self, birth_details: BirthDetails) -> Dict:
        """Calculate ascendant (rising sign)"""
        # Simplified calculation - real implementation would use sidereal time
        observer = ephem.Observer()
        observer.lat = str(birth_details.latitude)
        observer.lon = str(birth_details.longitude)
        observer.date = birth_details.birth_date
        
        # Calculate local sidereal time
        lst = observer.sidereal_time()
        lst_deg = float(lst) * 180 / math.pi
        
        # Calculate ascendant longitude
        lat_rad = math.radians(birth_details.latitude)
        asc_long = math.atan2(math.cos(lst_deg * math.pi/180), 
                             -math.sin(lst_deg * math.pi/180) * math.cos(lat_rad))
        asc_long = asc_long * 180 / math.pi
        
        # Apply ayanamsa correction
        ayanamsa = self.calculate_ayanamsa(birth_details.birth_date)
        asc_long -= ayanamsa
        
        return self.get_sign_and_degree(asc_long)
    
    def calculate_current_dasha(self, birth_details: BirthDetails) -> Dict:
        """Calculate current Mahadasha and Antardasha"""
        birth_moon = self.birth_chart.get('Moon', {})
        moon_nakshatra = self.get_nakshatra(birth_moon.get('degree', 0) + birth_moon.get('sign_num', 0) * 30)
        
        # Dasha starting planet based on birth nakshatra
        dasha_sequence = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
        nakshatra_lords = [
            "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
            "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
            "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"
        ]
        
        birth_nakshatra_index = moon_nakshatra['index']
        starting_dasha = nakshatra_lords[birth_nakshatra_index]
        
        # Calculate elapsed time since birth
        current_date = datetime.now()
        elapsed_years = (current_date - birth_details.birth_date).days / 365.25
        
        # Find current dasha
        total_elapsed = 0
        current_mahadasha = starting_dasha
        
        for i, planet in enumerate(dasha_sequence):
            if planet == starting_dasha:
                start_index = i
                break
        
        for i in range(9):  # Maximum 120 years cycle
            planet_index = (start_index + i) % 9
            planet = dasha_sequence[planet_index]
            period_years = self.DASHA_PERIODS[planet]
            
            if total_elapsed + period_years > elapsed_years:
                current_mahadasha = planet
                remaining_years = (total_elapsed + period_years) - elapsed_years
                break
            total_elapsed += period_years
        
        return {
            'mahadasha': current_mahadasha,
            'remaining_years': remaining_years,
            'birth_nakshatra': moon_nakshatra['name']
        }
    
    def get_nakshatra(self, longitude: float) -> Dict:
        """Get nakshatra from longitude"""
        nakshatra_span = 360 / 27  # Each nakshatra spans 13°20'
        nakshatra_index = int(longitude // nakshatra_span)
        
        return {
            'name': self.NAKSHATRAS[nakshatra_index],
            'index': nakshatra_index,
            'pada': int((longitude % nakshatra_span) // (nakshatra_span / 4)) + 1
        }
    
        # ...existing code...
    def generate_health_predictions(self, birth_details: BirthDetails) -> str:
        """Generate health predictions based on planetary positions"""
        
        predictions = []
        predictions.append("🏥 HEALTH FORECAST")
        predictions.append("=" * 50)
        
        # Analyze 6th house (health), Mars (energy), and current dasha
        sun_sign = self.birth_chart.get('Sun', {}).get('sign', 'Unknown')
        mars_sign = self.birth_chart.get('Mars', {}).get('sign', 'Unknown')
        current_dasha = self.current_dasha.get('mahadasha', 'Unknown')
        
        # Next 6 months predictions
        predictions.append("\n📅 NEXT 6 MONTHS (Aug 2025 - Jan 2026):")
        
        if current_dasha in ['Sun', 'Mars']:
            predictions.append("• Generally strong vitality and energy levels")
            predictions.append("• Watch for minor inflammation or heat-related issues")
            predictions.append("• Best months: September-October for physical activities")
        elif current_dasha in ['Moon', 'Venus']:
            predictions.append("• Focus on emotional well-being and stress management")
            predictions.append("• Possible minor digestive or hormonal fluctuations")
            predictions.append("• Best months: November-December for healing and recovery")
        else:
            predictions.append("• Moderate health trends with steady energy")
            predictions.append("• Pay attention to routine and preventive care")
        
        # Next 2 years predictions
        predictions.append("\n📅 NEXT 2 YEARS (2025-2027):")
        predictions.append("• Major Transit Influence: Jupiter and Saturn movements affecting long-term health")
        
        if mars_sign in ['Aries', 'Scorpio', 'Leo']:
            predictions.append("• Strong constitution with good recovery ability")
            predictions.append("• Watch periods: March-April 2026 (minor health attention needed)")
        else:
            predictions.append("• Steady health with focus on building immunity")
            predictions.append("• Favorable period: Oct 2026 - Feb 2027 for health improvements")
        
        # Physical and emotional indicators
        predictions.append("\n🧘 PHYSICAL & EMOTIONAL WELL-BEING:")
        dasha_health_effects = {
            'Sun': 'Strong vitality, watch heart and eyes',
            'Moon': 'Emotional sensitivity, focus on mental health',
            'Mars': 'High energy, prevent accidents and inflammation',
            'Mercury': 'Good nervous system, watch stress levels',
            'Jupiter': 'Generally positive, watch weight gain',
            'Venus': 'Good overall health, minor reproductive system attention',
            'Saturn': 'Build discipline, watch bones and chronic conditions',
            'Rahu': 'Unusual health patterns, avoid extremes',
            'Ketu': 'Spiritual healing beneficial, watch mysterious ailments'
        }
        predictions.append(f"• Current Dasha ({current_dasha}) suggests: {dasha_health_effects.get(current_dasha, 'Balanced health patterns')}")
        
        predictions.append(dasha_health_effects.get(current_dasha, 'Balanced health patterns'))
        
        return "\n".join(predictions)
    # ...existing code...    
    def generate_career_predictions(self, birth_details: BirthDetails) -> str:
        """Generate career and job predictions"""
        
        predictions = []
        predictions.append("💼 CAREER & JOB PROSPECTS")
        predictions.append("=" * 50)
        
        # Analyze 10th house (career), Saturn (discipline), Jupiter (growth)
        saturn_sign = self.birth_chart.get('Saturn', {}).get('sign', 'Unknown')
        jupiter_sign = self.birth_chart.get('Jupiter', {}).get('sign', 'Unknown')
        sun_sign = self.birth_chart.get('Sun', {}).get('sign', 'Unknown')
        current_dasha = self.current_dasha.get('mahadasha', 'Unknown')
        
        # Job stability and changes (12-24 months)
        predictions.append("\n📈 JOB STABILITY & CHANGES (Next 12-24 Months):")
        
        if current_dasha in ['Saturn', 'Jupiter']:
            predictions.append("• HIGH STABILITY: Current period favors steady career growth")
            predictions.append("• Promotion chances: 70% likely between Jan-Jun 2026")
            predictions.append("• Role changes: Natural progression rather than sudden shifts")
        elif current_dasha in ['Sun', 'Mars']:
            predictions.append("• DYNAMIC PERIOD: Leadership opportunities emerging")
            predictions.append("• Job changes: 60% chance of positive role transition by mid-2026")
            predictions.append("• Entrepreneurial ventures: Favorable period starting Oct 2025")
        else:
            predictions.append("• MODERATE STABILITY: Gradual improvements expected")
            predictions.append("• Focus on skill development and networking")
        
        # Favorable periods
        predictions.append("\n🌟 FAVORABLE PERIODS:")
        predictions.append("• Job Search: Sep-Nov 2025, Mar-May 2026")
        predictions.append("• Business Ventures: Oct 2025-Jan 2026, Jul-Sep 2026")
        predictions.append("• Relocation: Jupiter transit supports moves in Q2 2026")
        predictions.append("• Salary Negotiations: Dec 2025, Jun 2026")
        
        # Sector alignment
        predictions.append("\n🎯 ALIGNED SECTORS & ROLES:")
        
        planet_career_mapping = {
            'Sun': 'Government, Leadership, Administration, Politics',
            'Moon': 'Healthcare, Food, Hospitality, Public Service',
            'Mars': 'Engineering, Military, Sports, Real Estate',
            'Mercury': 'IT, Communication, Writing, Trade, Education',
            'Jupiter': 'Finance, Teaching, Law, Consulting, Spiritual',
            'Venus': 'Arts, Entertainment, Beauty, Luxury, Fashion',
            'Saturn': 'Manufacturing, Construction, Mining, Agriculture',
            'Rahu': 'Technology, Innovation, Foreign Trade, Research',
            'Ketu': 'Spirituality, Research, Healing, Technical Skills'
        }
        
        aligned_sectors = planet_career_mapping.get(current_dasha, 'Diverse opportunities')
        predictions.append(f"• Primary alignment: {aligned_sectors}")
        
        # Based on dominant planets
        if saturn_sign in ['Capricorn', 'Aquarius']:
            predictions.append("• Secondary strength: Management, systematic work, long-term projects")
        if jupiter_sign in ['Sagittarius', 'Pisces']:
            predictions.append("• Growth potential: Advisory roles, international work, education sector")
        
        return "\n".join(predictions)
    
    def generate_family_predictions(self, birth_details: BirthDetails) -> str:
        """Generate family and relationship predictions"""
        
        predictions = []
        predictions.append("👨‍👩‍👧‍👦 FAMILY & RELATIONSHIPS")
        predictions.append("=" * 50)
        
        # Analyze 4th house (family), 7th house (marriage), Venus (relationships)
        venus_sign = self.birth_chart.get('Venus', {}).get('sign', 'Unknown')
        moon_sign = self.birth_chart.get('Moon', {}).get('sign', 'Unknown')
        current_dasha = self.current_dasha.get('mahadasha', 'Unknown')
        
        # General family environment
        predictions.append("\n🏠 FAMILY ENVIRONMENT:")
        
        if current_dasha in ['Moon', 'Venus', 'Jupiter']:
            predictions.append("• HARMONIOUS PERIOD: Family relationships strengthening")
            predictions.append("• Emotional bonds deepening, good communication")
            predictions.append("• Possible family celebrations or gatherings")
        elif current_dasha in ['Mars', 'Saturn']:
            predictions.append("• STRUCTURED PHASE: Some tension but ultimately strengthening")
            predictions.append("• Need for patience in family matters")
            predictions.append("• Resolution of old family issues possible")
        else:
            predictions.append("• BALANCED DYNAMICS: Normal family interactions")
            predictions.append("• Focus on practical family matters")
        
        # Marriage and relationships
        predictions.append("\n💑 MARRIAGE & RELATIONSHIPS:")
        
        if venus_sign in ['Taurus', 'Libra', 'Pisces']:
            predictions.append("• Strong relationship potential in current period")
            predictions.append("• For singles: Meeting prospects likely in Q4 2025 or Q2 2026")
            predictions.append("• For married: Renewed romance and understanding")
        
        predictions.append("• Key relationship periods:")
        predictions.append("  - October-December 2025: New connections or deepening bonds")
        predictions.append("  - April-June 2026: Important relationship decisions")
        predictions.append("  - September-November 2026: Harmony and celebration")
        
        # Children and responsibilities
        predictions.append("\n👶 CHILDREN & HOUSEHOLD RESPONSIBILITIES:")
        
        if current_dasha == 'Jupiter':
            predictions.append("• EXCELLENT for family expansion or child-related matters")
            predictions.append("• Educational decisions for children go well")
            predictions.append("• Financial planning for family needs favorable")
        elif current_dasha == 'Moon':
            predictions.append("• Emotional connection with children strengthens")
            predictions.append("• Home improvements or relocations possible")
            predictions.append("• Motherly/nurturing role emphasized")
        
        predictions.append("\n📅 QUARTERLY HIGHLIGHTS:")
        predictions.append("• Q3 2025: Family harmony, possible reunions")
        predictions.append("• Q4 2025: Important family decisions, celebrations")
        predictions.append("• Q1 2026: New family responsibilities or changes")
        predictions.append("• Q2 2026: Relationship milestones, emotional fulfillment")
        
        # Parents and extended family
        predictions.append("\n👴👵 PARENTS & EXTENDED FAMILY:")
        predictions.append("• Generally supportive period with elder family members")
        predictions.append("• Possible health attention needed for elders in Q1 2026")
        predictions.append("• Family property or inheritance matters may surface")
        
        return "\n".join(predictions)
    
    def generate_complete_reading(self, birth_details: BirthDetails) -> str:
        """Generate complete horoscope reading"""
        
        # Calculate birth chart
        self.birth_chart = self.calculate_planetary_positions(birth_details)
        ascendant = self.calculate_ascendant(birth_details)
        self.current_dasha = self.calculate_current_dasha(birth_details)
        
        reading = []
        
        # Header
        reading.append("⭐" * 60)
        reading.append(f"    VEDIC ASTROLOGY READING FOR {birth_details.name.upper()}")
        reading.append("⭐" * 60)
        reading.append(f"Birth Date: {birth_details.birth_date.strftime('%d-%m-%Y')}")
        reading.append(f"Birth Time: {birth_details.birth_time}")
        reading.append(f"Birth Place: {birth_details.birth_place}")
        reading.append(f"Rising Sign: {ascendant.get('sign', 'Unknown')}")
        reading.append(f"Current Mahadasha: {self.current_dasha.get('mahadasha', 'Unknown')}")
        reading.append(f"Birth Nakshatra: {self.current_dasha.get('birth_nakshatra', 'Unknown')}")
        reading.append("\n")
        
        # Generate all predictions
        health_forecast = self.generate_health_predictions(birth_details)
        career_forecast = self.generate_career_predictions(birth_details)
        family_forecast = self.generate_family_predictions(birth_details)
        
        reading.append(health_forecast)
        reading.append("\n\n")
        reading.append(career_forecast)
        reading.append("\n\n")
        reading.append(family_forecast)
        
        # Summary and recommendations
        reading.append("\n\n🎯 KEY RECOMMENDATIONS & PRECAUTIONS (2025-2027)")
        reading.append("=" * 60)
        
        current_dasha = self.current_dasha.get('mahadasha', 'Unknown')
        
        reading.append("\n💡 PRIORITY ACTIONS:")
        if current_dasha in ['Jupiter', 'Venus']:
            reading.append("• Focus on growth, learning, and positive relationships")
            reading.append("• Excellent time for major life decisions")
            reading.append("• Invest in health and spiritual practices")
        elif current_dasha in ['Saturn', 'Mars']:
            reading.append("• Practice patience and disciplined approach")
            reading.append("• Build strong foundations in career and health")
            reading.append("• Avoid impulsive decisions, plan carefully")
        else:
            reading.append("• Maintain balance in all life areas")
            reading.append("• Focus on communication and adaptability")
            reading.append("• Regular health check-ups recommended")
        
        reading.append("\n⚠️ PERIODS TO WATCH:")
        reading.append("• March-April 2026: Extra care in health and relationships")
        reading.append("• August-September 2026: Career decisions need careful thought")
        reading.append("• December 2026: Family matters require attention")
        
        reading.append("\n🌟 MOST FAVORABLE PERIODS:")
        reading.append("• October-December 2025: Overall positive phase")
        reading.append("• May-July 2026: Career and financial growth")
        reading.append("• January-March 2027: Personal and spiritual development")
        
        reading.append("\n" + "=" * 60)
        reading.append("Reading generated using traditional Vedic astrology principles")
        reading.append("For specific concerns, consult with a qualified astrologer")
        reading.append("=" * 60)
        
        return "\n".join(reading)

def get_coordinates(city_name: str) -> Tuple[float, float]:
    """Get approximate coordinates for major cities"""
    city_coords = {
        'mumbai': (19.0760, 72.8777),
        'delhi': (28.7041, 77.1025),
        'bangalore': (12.9716, 77.5946),
        'chennai': (13.0827, 80.2707),
        'kolkata': (22.5726, 88.3639),
        'hyderabad': (17.3850, 78.4867),
        'pune': (18.5204, 73.8567),
        'ahmedabad': (23.0225, 72.5714),
        'jaipur': (26.9124, 75.7873),
        'lucknow': (26.8467, 80.9462),
        'new york': (40.7128, -74.0060),
        'london': (51.5074, -0.1278),
        'tokyo': (35.6762, 139.6503),
        'sydney': (-33.8688, 151.2093),
        'toronto': (43.6532, -79.3832)
    }
    
    city_lower = city_name.lower()
    return city_coords.get(city_lower, (28.7041, 77.1025))  # Default to Delhi

def parse_birth_details() -> BirthDetails:
    """Interactive function to get birth details from user"""
    print("🌟 VEDIC ASTROLOGY READING GENERATOR 🌟")
    print("=" * 50)
    
    name = input("Enter full name: ").strip()
    
    # Get birth date
    while True:
        try:
            birth_date_str = input("Enter birth date (DD-MM-YYYY): ").strip()
            birth_date = datetime.strptime(birth_date_str, "%d-%m-%Y")
            break
        except ValueError:
            print("Invalid date format. Please use DD-MM-YYYY")
    
    # Get birth time
    birth_time = input("Enter birth time (HH:MM AM/PM): ").strip()
    
    # Parse time for calculations
    try:
        time_obj = datetime.strptime(birth_time, "%I:%M %p")
        birth_datetime = birth_date.replace(
            hour=time_obj.hour,
            minute=time_obj.minute
        )
    except ValueError:
        try:
            time_obj = datetime.strptime(birth_time, "%H:%M")
            birth_datetime = birth_date.replace(
                hour=time_obj.hour,
                minute=time_obj.minute
            )
        except ValueError:
            print("Invalid time format. Using 12:00 PM as default.")
            birth_datetime = birth_date.replace(hour=12, minute=0)
    
    # Get birth place
    birth_place = input("Enter birth place (City, Country): ").strip()
    
    # Get coordinates
    lat, lon = get_coordinates(birth_place.split(',')[0].strip())
    
    return BirthDetails(
        name=name,
        birth_date=birth_datetime,
        birth_time=birth_time,
        birth_place=birth_place,
        latitude=lat,
        longitude=lon,
        timezone="UTC"  # Simplified for this example
    )

def main():
    """Main function to run the astrology reading generator"""
    try:
        # Get birth details
        birth_details = parse_birth_details()
        
        # Create astrology instance
        vedic_astro = VedicAstrology()
        
        print("\n🔮 Generating your personalized Vedic astrology reading...")
        print("Please wait while we calculate planetary positions and dashas...\n")
        
        # Generate complete reading
        reading = vedic_astro.generate_complete_reading(birth_details)
        
        # Display reading
        print(reading)
        
        # Option to save to file
        save_option = input("\nWould you like to save this reading to a file? (y/n): ").strip().lower()
        if save_option == 'y':
            filename = f"{birth_details.name.replace(' ', '_')}_vedic_reading.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(reading)
            print(f"Reading saved to {filename}")
        
    except KeyboardInterrupt:
        print("\n\nReading generation cancelled.")
    except Exception as e:
        print(f"\nError generating reading: {str(e)}")
        print("Please check your input and try again.")

if __name__ == "__main__":
    # Required packages installation note
    print("Required packages: ephem, pytz")
    print("Install with: pip install ephem pytz")
    print("-" * 40)
    
    main()