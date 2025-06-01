// Utility functions for generating random data
const randomData = {
    // Names
    firstNames: ['John', 'Jane', 'Michael', 'Sarah', 'David', 'Maria', 'James', 'Anna', 'Robert', 'Lisa', 'Juan', 'Maria', 'Pedro', 'Jose', 'Antonio'],
    middleInitials: ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O'],
    lastNames: ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Santos', 'Cruz', 'Reyes', 'Gonzales', 'Torres'],
    
    // Courses (from registration form)
    courses: [
        'Bachelor of Elementary Education',
        'Bachelor of Secondary Education Major in Math',
        'Bachelor of Technology and Livelihood Education Major in Home Economics',
        'Bachelor of Arts in English Language Studies',
        'Bachelor of Arts in Literature',
        'Bachelor of Science in Industrial Engineering',
        'Bachelor of Science in Information Technology',
        'Bachelor in Industrial Technology Major in Drafting Technology',
        'Bachelor in Industrial Technology Major in Electronics Technology',
        'Bachelor in Industrial Technology Major in Computer Technology',
        'Bachelor in Industrial Technology Major in Garments Technology',
        'Bachelor in Industrial Technology Major in Automotive Technology',
        'Bachelor of Science in Forestry',
        'Bachelor of Science in Agriculture Major in Animal Science',
        'Bachelor of Science in Agriculture Major in Horticulture',
        'Bachelor of Science in Agriculture Major in Agronomy',
        'Bachelor of Science in Agriculture Major in Crop Protection',
        'Bachelor of Science in Agriculture Major in Agricultural Economics',
        'Bachelor of Science in Hospitality Management',
        'Bachelor of Science in Tourism'
    ],

    // Blood types
    bloodTypes: ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', 'Unknown'],

    // Civil status
    civilStatus: ['Single', 'Married', 'Widowed', 'Separated'],

    // Cities in Cebu
    cities: ['Argao', 'Cebu City', 'Danao', 'Lapu-Lapu', 'Mandaue', 'Talisay', 'Toledo'],

    // Provinces
    provinces: ['Cebu', 'Bohol', 'Negros Oriental', 'Siquijor'],

    // Generate random date between 18-60 years ago
    getRandomBirthDate() {
        const today = new Date();
        const minAge = 18;
        const maxAge = 60;
        const randomAge = Math.floor(Math.random() * (maxAge - minAge + 1)) + minAge;
        const birthDate = new Date(today.getFullYear() - randomAge, 
            Math.floor(Math.random() * 12), 
            Math.floor(Math.random() * 28) + 1);
        return birthDate.toISOString().split('T')[0];
    },

    // Generate random height (150-190 cm)
    getRandomHeight() {
        return (Math.random() * 40 + 150).toFixed(2);
    },

    // Generate random weight (45-100 kg)
    getRandomWeight() {
        return (Math.random() * 55 + 45).toFixed(2);
    },

    // Generate random phone number
    getRandomPhone() {
        return '09' + Math.floor(Math.random() * 1000000000).toString().padStart(9, '0');
    },

    // Generate random postal code
    getRandomPostalCode() {
        return Math.floor(Math.random() * 9000 + 1000).toString();
    },

    // Generate random address
    getRandomAddress() {
        const streets = ['Main Street', 'Park Avenue', 'Quezon Boulevard', 'Rizal Street', 'Bonifacio Street'];
        const numbers = Math.floor(Math.random() * 999) + 1;
        return `${numbers} ${streets[Math.floor(Math.random() * streets.length)]}`;
    }
};

// Function to autofill registration form
function autofillRegistrationForm() {
    // Basic information
    document.getElementById('firstName').value = randomData.firstNames[Math.floor(Math.random() * randomData.firstNames.length)];
    document.getElementById('middleInitial').value = randomData.middleInitials[Math.floor(Math.random() * randomData.middleInitials.length)];
    document.getElementById('lastName').value = randomData.lastNames[Math.floor(Math.random() * randomData.lastNames.length)];
    
    // Role selection (randomly choose between student and faculty)
    const isStudent = Math.random() > 0.3; // 70% chance of being a student
    if (isStudent) {
        document.getElementById('studentRole').checked = true;
        document.getElementById('facultyRole').checked = false;
        
        // Student specific fields
        document.getElementById('sex').value = Math.random() > 0.5 ? 'M' : 'F';
        document.getElementById('yrLevel').value = Math.floor(Math.random() * 4) + 1;
        document.getElementById('studentIdNumber').value = Math.floor(Math.random() * 10000000).toString().padStart(7, '0');
        document.getElementById('lrn').value = Math.floor(Math.random() * 1000000000000).toString().padStart(12, '0');
        document.getElementById('course').value = randomData.courses[Math.floor(Math.random() * randomData.courses.length)];
    } else {
        document.getElementById('facultyRole').checked = true;
        document.getElementById('studentRole').checked = false;
        
        // Faculty specific fields
        document.getElementById('department').value = ['Computer Studies', 'Engineering', 'Education', 'Arts and Sciences'][Math.floor(Math.random() * 4)];
        document.getElementById('position').value = ['Professor', 'Associate Professor', 'Assistant Professor', 'Instructor'][Math.floor(Math.random() * 4)];
        document.getElementById('facultyIdNumber').value = Math.floor(Math.random() * 10000000).toString().padStart(7, '0');
    }

    // Common fields
    const firstName = document.getElementById('firstName').value.toLowerCase();
    const lastName = document.getElementById('lastName').value.toLowerCase();
    document.getElementById('email').value = `${firstName}.${lastName}@ctu.edu.ph`;
    
    // Generate a strong password
    const password = generateStrongPassword();
    document.getElementById('password').value = password;
    document.getElementById('confirmPassword').value = password;
}

// Function to autofill patient form
function autofillPatientForm() {
    // Personal Information
    document.getElementById('birth_date').value = randomData.getRandomBirthDate();
    document.getElementById('bloodtype').value = randomData.bloodTypes[Math.floor(Math.random() * randomData.bloodTypes.length)];
    document.getElementById('height').value = randomData.getRandomHeight();
    document.getElementById('weight').value = randomData.getRandomWeight();

    // Randomly select some medical conditions (with 30% probability for each)
    const medicalConditions = document.querySelectorAll('input[name="medical_history"]');
    medicalConditions.forEach(checkbox => {
        if (Math.random() < 0.3 && checkbox.value !== 'No Medical History') {
            checkbox.checked = true;
        }
    });

    // Randomly select some allergies (with 20% probability for each)
    const allergies = document.querySelectorAll('input[name="allergies"]');
    allergies.forEach(checkbox => {
        if (Math.random() < 0.2 && checkbox.value !== 'None') {
            checkbox.checked = true;
        }
    });

    // Randomly select some family history (with 25% probability for each)
    const familyHistory = document.querySelectorAll('input[name="family_history"]');
    familyHistory.forEach(checkbox => {
        if (Math.random() < 0.25 && checkbox.value !== 'No Family History') {
            checkbox.checked = true;
        }
    });

    // Randomly select some risk factors (with 15% probability for each)
    const riskFactors = document.querySelectorAll('input[name="risk_assessment"]');
    riskFactors.forEach(checkbox => {
        if (Math.random() < 0.15 && checkbox.value !== 'No Risk') {
            checkbox.checked = true;
        }
    });

    // Contact Details
    document.getElementById('home_address').value = randomData.getRandomAddress();
    document.getElementById('city').value = randomData.cities[Math.floor(Math.random() * randomData.cities.length)];
    document.getElementById('civil_status').value = randomData.civilStatus[Math.floor(Math.random() * randomData.civilStatus.length)];
    document.getElementById('country').value = 'Philippines';
    document.getElementById('state_province').value = randomData.provinces[Math.floor(Math.random() * randomData.provinces.length)];
    document.getElementById('postal_zipcode').value = randomData.getRandomPostalCode();
    document.getElementById('nationality').value = 'Filipino';

    // Emergency Contact
    const parentFirstName = randomData.firstNames[Math.floor(Math.random() * randomData.firstNames.length)];
    const parentLastName = randomData.lastNames[Math.floor(Math.random() * randomData.lastNames.length)];
    document.getElementById('parent_guardian').value = `${parentFirstName} ${parentLastName}`;
    document.getElementById('parent_guardian_contact').value = randomData.getRandomPhone();
}

// Function to generate a strong password
function generateStrongPassword() {
    const length = 12;
    const charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*(),.?\":{}|<>";
    let password = "";
    
    // Ensure at least one of each required character type
    password += "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[Math.floor(Math.random() * 26)]; // Uppercase
    password += "abcdefghijklmnopqrstuvwxyz"[Math.floor(Math.random() * 26)]; // Lowercase
    password += "0123456789"[Math.floor(Math.random() * 10)]; // Number
    password += "!@#$%^&*(),.?\":{}|<>"[Math.floor(Math.random() * 20)]; // Special

    // Fill the rest randomly
    for (let i = password.length; i < length; i++) {
        password += charset[Math.floor(Math.random() * charset.length)];
    }

    // Shuffle the password
    return password.split('').sort(() => Math.random() - 0.5).join('');
}

// Add autofill buttons to the forms
function addAutofillButtons() {
    // Add button to registration form if it exists
    const registrationForm = document.getElementById('registrationForm');
    if (registrationForm) {
        const autofillButton = document.createElement('button');
        autofillButton.type = 'button';
        autofillButton.className = 'bg-gray-500 text-white text-[14px] p-2 rounded-md w-fit px-5 cursor-pointer mt-4 mr-2';
        autofillButton.textContent = 'Autofill Form';
        autofillButton.onclick = autofillRegistrationForm;
        registrationForm.insertBefore(autofillButton, registrationForm.querySelector('input[type="submit"]'));
    }

    // Add button to patient form if it exists
    const patientForm = document.querySelector('form[method="POST"]');
    if (patientForm && document.getElementById('birth_date')) {
        const autofillButton = document.createElement('button');
        autofillButton.type = 'button';
        autofillButton.className = 'bg-gray-500 text-white text-[14px] p-2 rounded-md w-fit px-5 cursor-pointer mt-4 mr-2';
        autofillButton.textContent = 'Autofill Form';
        autofillButton.onclick = autofillPatientForm;
        patientForm.insertBefore(autofillButton, patientForm.querySelector('button[type="submit"]'));
    }
}

// Initialize when the document is loaded
document.addEventListener('DOMContentLoaded', addAutofillButtons); 