() => {
    const contacts = {};

    // Ищем email
    const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;
    const emailMatch = document.body.textContent.match(emailRegex);
    if (emailMatch) {
        contacts.email = emailMatch[0];
    }

    // Ищем телефон
    const phoneRegex = /(\+?61|0)[-\s\.]?\(?[0-9]{1,4}\)?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,4}/g;
    const phoneMatch = document.body.textContent.match(phoneRegex);
    if (phoneMatch) {
        contacts.phone = phoneMatch[0];
    }

    return Object.keys(contacts).length > 0 ? contacts : null;
}
