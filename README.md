# GroceriStore-Application

## Project Overview

Welcome to the GroceriStore-Application, a modern platform designed to provide users with a seamless shopping experience for all their grocery needs. This innovative application not only simplifies the process of purchasing groceries but also offers features such as order tracking, payment history, and personalized profiles for enhanced convenience.

## Project Goals

The Groceries Store Application aims to achieve the following objectives:

- **Intuitive Design:** Develop an easy-to-navigate and visually appealing online grocery store.
- **User Profiles:** Implement user profiles with features like order history, payment information storage.
- **Product Management:** Enable efficient management of grocery products, including adding, editing, and categorizing items.
- **Shopping Cart:** Provide users with a user-friendly shopping cart to manage their purchases.
- **Checkout Process:** Implement a seamless checkout process with various payment options and order confirmation.
- **Order Tracking:** Enable users to track the status of their orders in real-time.
- **Admin Dashboard:** Develop a dashboard for administrators to manage products, orders, users, and other aspects of the platform.
- **Data Security:** Ensure the security of user data and payment information through encryption and secure protocols.
- **Responsive Design:** Create a responsive design that works smoothly across various devices and screen sizes.

## Technology Stack

The Groceries Store Application utilizes the following technologies and tools:

- **Flask:** A robust Python web framework for scalable web applications.
- **SQLite:** A lightweight and efficient relational database system, ideal for managing music data.
- **HTML:** The standard markup language for structuring web content.
- **TAILWINDCSS:** A utility-first CSS framework for designing and styling web pages.
- **JavaScript:** A versatile scripting language for adding interactivity and dynamic features.
- **RazorPay API:** A RazorPay API allows user to seamlessly go through Payments

## How to Run the Web App Locally

To run the Groceries Store Application locally on your machine, follow these steps:

1. **Clone the Repository:**
    ```bash
    git clone https://github.com/Jeevanchoudhary9/GroceriStore-Application.git
    ```
2. **Create .env file:**
   
    Insert the following code in the file:
   ```bash
    FLASK_DEBUG=true
    FLASK_APP=app.py
    SQLALCHEMY_DATABASE_URI=sqlite:///db.sqlite3
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    SECRET_KEY="Code"
   ```
   **Create Secret Key(To be run in Terminal):**
    ```bash
    echo “SECRET_KEY=$(date +%s%N) | shamus -a 512 | cut -d' ' -f1)">>env
    ```
     put the secret key in .env at "Code"
   
4. **Navigate to the Project Directory:**
    ```bash
    cd GroceriStore-Application
    ```

5. **Create a Virtual Environment:**
    ```bash
    python3 -m venv env
    ```

6. **Activate the Virtual Environment:**
    ```bash
    source env/bin/activate
    ```

7. **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

8. **Run the Development Server:**
    ```bash
    flask run
    ```
    
9. **Access the Application:**
   Open your web browser and go to http://127.0.0.1:5000 or web shown in terminal

## Project Structure

```bash
Music Streaming Application/
    ├── instance/
    |   └──  db.sqlite3
    ├── static/
    |   └──  css/
    |        └──  style.css
    ├── templates/
    |   ├── cart/
    |   |   ├── buy_product.html
    |   |   ├── cart.html
    |   |   └── review_product.html
    |   ├── category/
    |   |   ├── add_category.html
    |   |   ├── delete_category.html
    |   |   └── edit_category.html
    |   ├── product/
    |   |   ├── add_product.html
    |   |   ├── delete_product.html
    |   |   └── edit_product.html
    |   ├── buy_payment.html
    |   ├── gs .png
    |   ├── gs.png
    |   ├── index.html
    |   ├── layout.html
    |   ├── login_man.html
    |   ├── login.html
    |   ├── manager_index.html
    |   ├── manager_layout.html
    |   ├── manager_navbar.html
    |   ├── navbar.html
    |   ├── order_success.html
    |   ├── order.html
    |   ├── payment.html
    |   ├── profile.html
    |   ├── register.html
    |   ├── success.html
    |   ├── summary.html
    |   ├── tail.html
    |   └── tracking.html
    ├── .env
    ├── app.py
    ├── config.py
    ├── models.py
    ├── README.md
    ├── requirements.txt
    └── routes.py
```

## Screenshots
![Login](https://github.com/Jeevanchoudhary9/GroceriStore-Application/blob/9deed43926d221c805daa7e5923497f5d34b4c47/screenshots/login.png)
*Caption: Login*

![User Register](https://github.com/Jeevanchoudhary9/GroceriStore-Application/blob/9deed43926d221c805daa7e5923497f5d34b4c47/screenshots/register.png)
*Caption: User Register*

![User Dashboard](https://github.com/Jeevanchoudhary9/GroceriStore-Application/blob/9deed43926d221c805daa7e5923497f5d34b4c47/screenshots/user%20dashboard.png)
*Caption: User Dashboard*

![Add To Cart](https://github.com/Jeevanchoudhary9/GroceriStore-Application/blob/9deed43926d221c805daa7e5923497f5d34b4c47/screenshots/add%20to%20cart.png)
*Caption: Add To Cart*

![Cart](https://github.com/Jeevanchoudhary9/GroceriStore-Application/blob/9deed43926d221c805daa7e5923497f5d34b4c47/screenshots/cart.png)
*Caption: Cart*

![Payment](https://github.com/Jeevanchoudhary9/GroceriStore-Application/blob/9deed43926d221c805daa7e5923497f5d34b4c47/screenshots/payment.png)
*Caption: Payment*

![History](https://github.com/Jeevanchoudhary9/GroceriStore-Application/blob/9deed43926d221c805daa7e5923497f5d34b4c47/screenshots/history.png)
*Caption: History*

![Admin Dashboard](https://github.com/Jeevanchoudhary9/GroceriStore-Application/blob/9deed43926d221c805daa7e5923497f5d34b4c47/screenshots/admin%20dashboard.png)
*Caption: Admin Dashboard*

![Admin Summary](https://github.com/Jeevanchoudhary9/GroceriStore-Application/blob/9deed43926d221c805daa7e5923497f5d34b4c47/screenshots/admin%20summary.png)
*Caption: Admin Summary*

## Conclusion

With its user-friendly interface, robust features, and secure payment options, the Groceries Store Application offers a convenient and enjoyable shopping experience for users. Whether it's browsing for products, managing orders, or tracking deliveries, this platform caters to the diverse needs of modern shoppers.

## Document Author

Jeevan Choudhary
