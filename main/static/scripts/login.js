document.addEventListener('DOMContentLoaded', function() {
    // Password toggle functionality
    const togglePassword = document.getElementById('togglePassword');
    const passwordInput = document.getElementById('password');
    const showIcon = document.getElementById('showIcon');
    const hideIcon = document.getElementById('hideIcon');

    if (togglePassword && passwordInput) {
        togglePassword.addEventListener('click', function() {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            showIcon.style.display = type === 'password' ? 'block' : 'none';
            hideIcon.style.display = type === 'password' ? 'none' : 'block';
        });
    }

    // Login form submission
    const loginForm = document.getElementById('loginForm');
    const otpForm = document.getElementById('otpForm');

    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            
            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Show OTP form and hide login form
                    loginForm.classList.add('hidden');
                    otpForm.classList.remove('hidden');
                    
                    // Focus on first OTP input
                    document.querySelector('#otpForm input[name="otp"]').focus();
                    
                    // Show success message
                    Swal.fire({
                        icon: 'success',
                        title: 'Success!',
                        text: data.message || 'Please check your email for the verification code'
                    });
                } else {
                    Swal.fire({
                        icon: 'error',
                        title: 'Login Failed',
                        text: data.message || 'Invalid credentials'
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: 'An error occurred during login'
                });
            });
        });
    }

    // OTP input handling is now in the template file's script block
});