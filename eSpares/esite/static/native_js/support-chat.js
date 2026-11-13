(() => {
    const thread = document.querySelector('.chat-thread-page[data-messages-url]');
    const list = document.getElementById('chat-thread-messages');
    const status = document.getElementById('chat-poll-status');
    if (!thread || !list || !status) return;

    let lastId = Math.max(0, ...Array.from(list.querySelectorAll('[data-message-id]'), node => Number(node.dataset.messageId) || 0));
    let stopped = thread.dataset.status !== 'open';

    const appendMessage = (message) => {
        if (!message || !Number.isInteger(message.id) || message.id <= lastId) return;
        const article = document.createElement('article');
        article.className = `chat-message${message.staff ? ' chat-message-staff' : ''}`;
        article.dataset.messageId = String(message.id);
        const author = document.createElement('strong');
        author.textContent = message.sender || (message.staff ? 'Support team' : 'Customer');
        const body = document.createElement('p');
        body.textContent = message.body || '';
        const time = document.createElement('time');
        const sentAt = new Date(message.sent_at);
        time.dateTime = sentAt.toISOString();
        time.textContent = sentAt.toLocaleString();
        article.append(author, body, time);
        list.append(article);
        lastId = message.id;
    };

    const refresh = async () => {
        try {
            const url = new URL(thread.dataset.messagesUrl, window.location.origin);
            url.searchParams.set('after', String(lastId));
            const response = await fetch(url, { credentials: 'same-origin', cache: 'no-store', headers: { Accept: 'application/json' } });
            if (!response.ok) throw new Error('Could not refresh chat.');
            const data = await response.json();
            (data.messages || []).forEach(appendMessage);
            if (data.status !== 'open') {
                stopped = true;
                status.textContent = 'This conversation is closed.';
                document.querySelectorAll('.chat-reply-form textarea, .chat-reply-form button').forEach(control => { control.disabled = true; });
            } else {
                status.textContent = 'New replies refresh automatically while this page is open.';
            }
            if (data.messages && data.messages.length) list.scrollTop = list.scrollHeight;
        } catch {
            status.textContent = 'Chat updates could not be refreshed. Check your connection or reload the page.';
        }
    };

    list.scrollTop = list.scrollHeight;
    window.setInterval(() => { if (!stopped) refresh(); }, 10000);
})();
