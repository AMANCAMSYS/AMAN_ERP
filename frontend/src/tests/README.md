# اختبارات الواجهة الأمامية - Frontend Tests

## الإعداد

```bash
cd frontend
npm install --save-dev vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
```

## تشغيل الاختبارات

```bash
# جميع الاختبارات
npm run test

# مع التغطية
npm run test:coverage

# في وضع المراقبة
npm run test:watch
```

## هيكل الاختبارات

```
src/tests/
├── setup.js              # إعداد الاختبارات
├── components/           # اختبارات المكونات
├── pages/                # اختبارات الصفحات
├── utils/                # اختبارات الأدوات المساعدة
└── e2e/                  # اختبارات End-to-End
```

## أمثلة

### اختبار مكون بسيط

```javascript
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import MyComponent from '../components/MyComponent'

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })
})
```

### اختبار تفاعل المستخدم

```javascript
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import LoginForm from '../pages/Login'

describe('LoginForm', () => {
  it('submits form correctly', async () => {
    const user = userEvent.setup()
    render(<LoginForm />)
    
    await user.type(screen.getByLabelText('Username'), 'testuser')
    await user.type(screen.getByLabelText('Password'), 'password123')
    await user.click(screen.getByRole('button', { name: 'Login' }))
    
    // التحقق من النتيجة
  })
})
```
