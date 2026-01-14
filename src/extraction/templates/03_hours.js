() => {
    // Ищем таблицы или списки с часами работы
    const selectors = [
        '.hours', '.opening-hours', '.business-hours',
        '[data-hours]', '.schedule', '.timetable'
    ];

    for (const selector of selectors) {
        const element = document.querySelector(selector);
        if (element) {
            return element.textContent.trim();
        }
    }

    return null;
}
