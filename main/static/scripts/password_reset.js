document.addEventListener('DOMContentLoaded', function() {
    const toggleNewPassword = document.querySelector('#toggleNewPassword');
    const newPasswordInput = document.querySelector('#new_password');
    const showNewPassIcon = document.querySelector('#showNewPassIcon');
    const hideNewPassIcon = document.querySelector('#hideNewPassIcon');

    toggleNewPassword.addEventListener('click', function (e) {
        const type = newPasswordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        newPasswordInput.setAttribute('type', type);
        if (type === 'password') {
            showNewPassIcon.style.display = 'block';
            hideNewPassIcon.style.display = 'none';
        } else {
            showNewPassIcon.style.display = 'none';
            hideNewPassIcon.style.display = 'block';
        }
    });

    const toggleConfirmPassword = document.querySelector('#toggleConfirmPassword');
    const confirmPasswordInput = document.querySelector('#confirm_password');
    const showConfirmPassIcon = document.querySelector('#showConfirmPassIcon');
    const hideConfirmPassIcon = document.querySelector('#hideConfirmPassIcon');

    toggleConfirmPassword.addEventListener('click', function (e) {
        const type = confirmPasswordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        confirmPasswordInput.setAttribute('type', type);
        if (type === 'password') {
            showConfirmPassIcon.style.display = 'block';
            hideConfirmPassIcon.style.display = 'none';
        } else {
            showConfirmPassIcon.style.display = 'none';
            hideConfirmPassIcon.style.display = 'block';
        }
    });
}); 