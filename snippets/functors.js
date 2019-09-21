function foo() {
    function bar() {
        setTimeout(() => console.log("1"), 1000);
    }
    console.log("2");
    return bar;
}

let x = foo();
x();
console.log("3");
