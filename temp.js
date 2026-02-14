function debounce(func, delay) {
    let timer;
    return(...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => {
            func(...args), delay
        });
    };
}
const debouncedResult = debounce((msg) => {
    console.log(msg);
}, 500);
debouncedResult("A");
debouncedResult("B");
debouncedResult("C");