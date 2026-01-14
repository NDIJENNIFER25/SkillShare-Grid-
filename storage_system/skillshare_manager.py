"""
SkillShare Connect Manager
Handles teachers, courses, bookings, and student management
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import uuid
import time

class SkillShareManager:
    def __init__(self, data_path: str = "storage_system/skillshare_data"):
        self.data_path = Path(data_path)
        self.data_path.mkdir(parents=True, exist_ok=True)

        # Data files
        self.teachers_file = self.data_path / "teachers.json"
        self.courses_file = self.data_path / "courses.json"
        self.bookings_file = self.data_path / "bookings.json"
        self.students_file = self.data_path / "students.json"

        # Load data
        self.teachers = self._load_json(self.teachers_file, self._get_default_teachers())
        self.courses = self._load_json(self.courses_file, self._get_default_courses())
        self.bookings = self._load_json(self.bookings_file, [])
        self.students = self._load_json(self.students_file, [])

    def _load_json(self, file_path: Path, default_data):
        """Load JSON data from file"""
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            self._save_json(file_path, default_data)
            return default_data

    def _save_json(self, file_path: Path, data):
        """Save JSON data to file"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _get_default_teachers(self) -> List[Dict]:
        """Get default teacher data"""
        return [
            {
                "id": "teacher_001",
                "name": "Chief Nkeng",
                "skill": "Traditional Carpentry",
                "description": "Retired master carpenter with 35 years of experience",
                "price_per_session": 2000,
                "currency": "FCFA",
                "rating": 4.8,
                "total_students": 45,
                "location": "Yaoundé",
                "region": "Centre",
                "available_days": ["Saturday", "Sunday"],
                "available_times": ["09:00-12:00", "14:00-17:00"],
                "profile_image": "chief_nkeng.jpg",
                "skills_offered": ["Furniture Making", "Wood Carving", "Tool Maintenance"],
                "languages": ["French", "English", "Ewondo"],
                "joined_date": "2024-01-15"
            },
            {
                "id": "teacher_002",
                "name": "Madame Fotso",
                "skill": "Tailoring & Fashion Design",
                "description": "Expert seamstress specializing in traditional and modern fashion",
                "price_per_session": 1500,
                "currency": "FCFA",
                "rating": 4.9,
                "total_students": 67,
                "location": "Douala",
                "region": "Littoral",
                "available_days": ["Monday", "Wednesday", "Friday"],
                "available_times": ["10:00-13:00", "15:00-18:00"],
                "profile_image": "madame_fotso.jpg",
                "skills_offered": ["Dress Making", "Pattern Design", "Alterations"],
                "languages": ["French", "Duala"],
                "joined_date": "2024-02-01"
            }
        ]

    def _get_default_courses(self) -> List[Dict]:
        """Get default course data"""
        return [
            {
                "id": "course_001",
                "title": "Carpentry Fundamentals",
                "teacher_id": "teacher_001",
                "teacher_name": "Chief Nkeng",
                "description": "Learn the basics of woodworking",
                "duration": "8 weeks",
                "sessions_per_week": 2,
                "total_sessions": 16,
                "price": 25000,
                "currency": "FCFA",
                "category": "Carpentry",
                "level": "Beginner",
                "materials": [
                    {"name": "Introduction Video", "size": "450MB", "type": "video", "chunks": 45}
                ],
                "enrolled_students": 23,
                "max_students": 30,
                "nodes_replicated": ["us-east", "eu-west"],
                "created_date": "2024-01-20"
            }
        ]

    def get_all_teachers(self, location: Optional[str] = None,
                        skill: Optional[str] = None) -> List[Dict]:
        """Get all teachers, optionally filtered"""
        teachers = self.teachers

        if location:
            teachers = [t for t in teachers if t.get("location") == location]

        if skill:
            teachers = [t for t in teachers if skill.lower() in t.get("skill", "").lower()]

        return teachers

    def get_teacher_by_id(self, teacher_id: str) -> Optional[Dict]:
        """Get teacher by ID"""
        for teacher in self.teachers:
            if teacher["id"] == teacher_id:
                return teacher
        return None

    def get_all_courses(self, teacher_id: Optional[str] = None,
                       category: Optional[str] = None) -> List[Dict]:
        """Get all courses, optionally filtered"""
        courses = self.courses

        if teacher_id:
            courses = [c for c in courses if c.get("teacher_id") == teacher_id]

        if category:
            courses = [c for c in courses if c.get("category") == category]

        return courses

    def get_course_by_id(self, course_id: str) -> Optional[Dict]:
        """Get course by ID"""
        for course in self.courses:
            if course["id"] == course_id:
                return course
        return None

    def create_booking(self, student_id: str, teacher_id: str,
                      session_date: str, session_time: str) -> Dict:
        """Create a new booking"""
        booking_id = f"booking_{str(uuid.uuid4())[:8]}"

        booking = {
            "id": booking_id,
            "student_id": student_id,
            "teacher_id": teacher_id,
            "session_date": session_date,
            "session_time": session_time,
            "status": "pending",
            "created_at": time.time(),
            "payment_status": "unpaid"
        }

        self.bookings.append(booking)
        self._save_json(self.bookings_file, self.bookings)

        return booking

    def get_bookings(self, student_id: Optional[str] = None,
                    teacher_id: Optional[str] = None) -> List[Dict]:
        """Get bookings, optionally filtered"""
        bookings = self.bookings

        if student_id:
            bookings = [b for b in bookings if b.get("student_id") == student_id]

        if teacher_id:
            bookings = [b for b in bookings if b.get("teacher_id") == teacher_id]

        return bookings

    def get_statistics(self) -> Dict:
        """Get platform statistics"""
        return {
            "total_teachers": len(self.teachers),
            "total_courses": len(self.courses),
            "total_students": len(self.students),
            "total_bookings": len(self.bookings),
            "pending_bookings": len([b for b in self.bookings if b["status"] == "pending"]),
            "completed_bookings": len([b for b in self.bookings if b["status"] == "completed"]),
            "total_course_materials": sum(len(c.get("materials", [])) for c in self.courses),
            "avg_teacher_rating": sum(t.get("rating", 0) for t in self.teachers) / len(self.teachers) if self.teachers else 0
        }