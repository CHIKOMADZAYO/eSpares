(() => {
    const track = document.getElementById('brand-carousel-track');
    const previous = document.getElementById('brand-carousel-prev');
    const next = document.getElementById('brand-carousel-next');

    if (!track || !previous || !next) return;

    const updateControls = () => {
        const maxScroll = track.scrollWidth - track.clientWidth;
        previous.disabled = track.scrollLeft <= 1;
        next.disabled = maxScroll <= 1 || track.scrollLeft >= maxScroll - 1;
    };

    const scrollByCard = (direction) => {
        const card = track.querySelector('.brand-carousel-card');
        if (!card) return;

        const gap = parseFloat(window.getComputedStyle(track).columnGap) || 0;
        const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        track.scrollBy({
            left: direction * (card.getBoundingClientRect().width + gap),
            behavior: reduceMotion ? 'auto' : 'smooth',
        });
    };

    previous.addEventListener('click', () => scrollByCard(-1));
    next.addEventListener('click', () => scrollByCard(1));
    track.addEventListener('scroll', updateControls, { passive: true });
    window.addEventListener('resize', updateControls);
    updateControls();
})();
