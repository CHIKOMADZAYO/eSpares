const email = document.querySelector('input[name="{{ form.username.html_name }}"]');
const password = document.querySelector('input[name="{{ form.password.html_name }}"]');
const button = document.querySelector('.login-button');
email.addEventListener('input', () => {
    const hasValue = email.value.trim().length > 0;
    password.classList.toggle('visually-hidden', !hasValue);
    password.required = hasValue;
    button.disabled = !hasValue || !password.value;
});
password.addEventListener('input', () => { button.disabled = !email.value.trim() || !password.value; });
if (email.value) { password.classList.remove('visually-hidden'); }
