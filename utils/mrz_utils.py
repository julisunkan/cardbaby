import re
from datetime import datetime

class MRZGenerator:
    """Generate Machine-Readable Zone (MRZ) for ID cards"""
    
    @staticmethod
    def generate_id_number():
        """Generate a unique ID number in format: ID-YYYYMMDD-XXXXX"""
        import random
        date_part = datetime.now().strftime('%Y%m%d')
        random_part = random.randint(10000, 99999)
        return f"ID{date_part}{random_part}"
    
    @staticmethod
    def format_mrz(full_name, id_number, date_of_birth, expiry_date):
        """
        Generate MRZ as a single line
        """
        # Line 1 parts
        name_parts = full_name.upper().split()
        surname = name_parts[0] if name_parts else "UNKNOWN"
        given_names = "".join(name_parts[1:]) if len(name_parts) > 1 else ""
        name_str = f"{surname}<<{given_names}"
        name_str = name_str[:39].ljust(39, '<')
        line1 = f"IDXXX{name_str}"
        
        # Line 2 parts
        dob_str = datetime.strptime(date_of_birth, '%Y-%m-%d').strftime('%y%m%d')
        exp_str = datetime.strptime(expiry_date, '%Y-%m-%d').strftime('%y%m%d')
        id_formatted = id_number.replace("-", "").upper()[-9:].ljust(9, '0')
        check_digit = MRZGenerator._calculate_check_digit(f"{id_formatted}{dob_str}")
        line2 = f"{id_formatted}{check_digit}{dob_str}0{exp_str}<<<<<<<<<<<"
        line2 = line2[:44]
        
        return f"{line1} {line2}"
    
    @staticmethod
    def _calculate_check_digit(data):
        """Calculate a simple check digit"""
        weights = [7, 3, 1]
        total = 0
        for i, char in enumerate(data):
            if char.isdigit():
                digit = int(char)
            else:
                # A=10, B=11, ..., Z=35
                digit = ord(char) - ord('A') + 10
            total += digit * weights[i % 3]
        return str(total % 10)
