document.addEventListener('DOMContentLoaded', function() {
    // Function to handle 'None' checkbox logic for mutually exclusive selection
    function handleNoneCheckbox(noneId, groupName, otherDivClass) {
        const noneCheckbox = document.getElementById(noneId);
        const otherCheckboxes = document.querySelectorAll(`input[name="${groupName}"]:not(#${noneId})`);
        const otherDiv = otherDivClass ? document.querySelector(`.${otherDivClass}`) : null;

        if (noneCheckbox) {
            noneCheckbox.addEventListener('change', function() {
                if (this.checked) {
                    otherCheckboxes.forEach(cb => cb.checked = false);
                    if (otherDiv) otherDiv.style.display = 'none';
                }
            });

            otherCheckboxes.forEach(checkbox => {
                checkbox.addEventListener('change', function() {
                    if (this.checked) {
                        noneCheckbox.checked = false;
                        if (otherDiv) otherDiv.style.display = 'block';
                    }
                    // Hide other div if no checkboxes are checked
                    const anyChecked = Array.from(otherCheckboxes).some(cb => cb.checked);
                    if (!anyChecked && otherDiv) otherDiv.style.display = 'none';
                });
            });
        }
    }

    // Initialize checkbox handlers for each section with correct IDs
    handleNoneCheckbox('allergy_none', 'allergies', 'other-allergies');
    handleNoneCheckbox('history_none', 'medical_history');
    handleNoneCheckbox('family_none', 'family_history', 'other-family-conditions-input');
    handleNoneCheckbox('risk_none', 'risk_assessment', 'pwd_specification_input');

    // Special handler for PWD checkbox
    const pwdCheckbox = document.getElementById('pwd');
    const pwdDetails = document.querySelector('.pwd-details');
    if (pwdCheckbox && pwdDetails) {
        pwdCheckbox.addEventListener('change', function() {
            pwdDetails.style.display = this.checked ? 'block' : 'none';
        });
    }

    // Add this to your existing DOMContentLoaded event listener
    const contactInput = document.getElementById('parent_guardian_contact');
    if (contactInput) {
        contactInput.addEventListener('input', function(e) {
            let value = e.target.value;
            
            // Remove any non-numeric characters
            value = value.replace(/[^0-9]/g, '');
            
            // Ensure it starts with '09'
            if (value.length >= 2 && !value.startsWith('09')) {
                value = '09' + value.slice(2);
            }
            
            // Limit to 11 digits
            value = value.slice(0, 11);
            
            // Update input value
            e.target.value = value;
        });
    }

    // Show/hide 'Other Medical Conditions' input
    const otherConditionsCheckbox = document.getElementById('other_conditions');
    const otherConditionsInput = document.getElementById('other_conditions_input');
    if (otherConditionsCheckbox && otherConditionsInput) {
        otherConditionsCheckbox.addEventListener('change', function() {
            otherConditionsInput.style.display = this.checked ? 'block' : 'none';
            if (!this.checked) {
                document.getElementById('other_medical').value = '';
            }
        });
    }

    // Show/hide 'Other Family Medical Conditions' input
    const otherFamilyConditionsCheckbox = document.getElementById('other_family_conditions');
    const otherFamilyConditionsInput = document.getElementById('other_family_conditions_input');
    if (otherFamilyConditionsCheckbox && otherFamilyConditionsInput) {
        otherFamilyConditionsCheckbox.addEventListener('change', function() {
            otherFamilyConditionsInput.style.display = this.checked ? 'block' : 'none';
            if (!this.checked) {
                document.getElementById('other_family_medical').value = '';
            }
        });
    }

    // Debug log for Family Medical History Other Medical Conditions
    console.log('other_family_conditions:', document.getElementById('other_family_conditions'), document.getElementById('other_family_conditions_input'));
});