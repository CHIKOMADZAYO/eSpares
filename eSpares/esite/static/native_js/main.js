// The login form exists only on the login page. Guard it so shared pages do
// not try to attach login handlers to missing elements.
const usernameInput = document.querySelector('.login-panel input[name="username"]');
const passwordInput = document.querySelector('.login-panel input[name="password"]');
const loginButton = document.querySelector('.login-panel .login-button');

if (usernameInput && passwordInput && loginButton) {
    const updateLoginState = () => {
        const hasUsername = usernameInput.value.trim().length > 0;
        passwordInput.classList.toggle('visually-hidden', !hasUsername);
        passwordInput.required = hasUsername;
        loginButton.disabled = !hasUsername || !passwordInput.value;
    };

    usernameInput.addEventListener('input', updateLoginState);
    passwordInput.addEventListener('input', updateLoginState);
    updateLoginState();
}
