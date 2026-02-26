# Quality Gate Reference — SOLID & Code Smells

## SOLID Principles — Detailed Guide

### S — Single Responsibility Principle
**A class should have only one reason to change.**

❌ Violation:
```javascript
class UserService {
  getUser(id) { /* DB query */ }
  sendWelcomeEmail(user) { /* Email logic */ }
  generateReport(users) { /* Report logic */ }
}
```

✅ Fixed:
```javascript
class UserRepository { getUser(id) { /* DB query only */ } }
class EmailService { sendWelcomeEmail(user) { /* Email only */ } }
class ReportService { generateReport(users) { /* Report only */ } }
```

---

### O — Open/Closed Principle
**Open for extension, closed for modification.**

❌ Violation:
```javascript
function calculateDiscount(type) {
  if (type === 'vip') return 0.2;
  if (type === 'regular') return 0.1;
  // Adding new type requires modifying this function
}
```

✅ Fixed:
```javascript
const discountStrategies = {
  vip: () => 0.2,
  regular: () => 0.1,
};
function calculateDiscount(type) {
  return discountStrategies[type]?.() ?? 0;
}
```

---

### L — Liskov Substitution Principle
**Subclasses must be substitutable for their base classes.**

❌ Violation:
```javascript
class Bird { fly() {} }
class Penguin extends Bird {
  fly() { throw new Error("Penguins can't fly!"); }
}
```

✅ Fixed:
```javascript
class Bird {}
class FlyingBird extends Bird { fly() {} }
class Penguin extends Bird { swim() {} }
```

---

### I — Interface Segregation Principle
**No code should be forced to depend on methods it doesn't use.**

❌ Violation:
```javascript
interface Worker {
  work(): void;
  eat(): void; // Robots don't eat!
}
```

✅ Fixed:
```javascript
interface Workable { work(): void; }
interface Eatable { eat(): void; }
class Robot implements Workable { work() {} }
class Human implements Workable, Eatable { work() {} eat() {} }
```

---

### D — Dependency Inversion Principle
**Depend on abstractions, not concretions.**

❌ Violation:
```javascript
class OrderService {
  constructor() {
    this.db = new MySQLDatabase(); // Hard dependency on concrete class
  }
}
```

✅ Fixed:
```javascript
class OrderService {
  constructor(database) { // Depends on abstraction (injected)
    this.db = database;
  }
}
```

---

## Code Smells — Detection & Fix

### 1. Long Method
**Symptom:** Method > 20 lines with multiple responsibilities
**Fix:** Extract to smaller, named methods

### 2. Magic Numbers/Strings
**Symptom:** `if (status === 3)` or `setTimeout(fn, 86400000)`
**Fix:** `const MAX_DAYS = 86400000; const STATUS_ACTIVE = 3;`

### 3. Deep Nesting
**Symptom:** 3+ levels of if/for nesting
**Fix:** Early returns, extract methods, reduce conditions

### 4. Duplicate Code
**Symptom:** Same logic copy-pasted in 2+ places
**Fix:** Extract to shared utility/service

### 5. God Object
**Symptom:** One class with 500+ lines, 30+ methods
**Fix:** Apply SRP, split into focused classes

### 6. Dead Code
**Symptom:** Commented-out code, unused variables/functions
**Fix:** Remove entirely

### 7. Poor Naming
**Symptom:** `const d = new Date()`, `function proc(x)`
**Fix:** `const createdAt = new Date()`, `function processOrder(order)`