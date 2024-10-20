# Go1 Commerce

Go1Commerce is a comprehensive e-commerce solution designed to empower businesses to build and manage their online stores with ease and flexibility. This open-source platform provides a range of features for managing products, orders, payments, and marketing, along with powerful SEO tools and analytics for optimizing your store's performance.


** Note: It's a standalone frappe E-commerce application and not compatible with ERPnext. 


## Key Features

- **Product Catalog Management**: Efficiently manage, showcase, and optimize your product offerings to drive customer engagement and sales.
- **Order Processing and Fulfillment**: Manage the entire order lifecycle, from checkout to delivery, with robust tracking and customer communication tools.
- **Payment Gateway**: Flexible and secure payment processing to cater to diverse customer preferences.
- **Search Engine Optimization (SEO) Toolkit**: Enhance your store's visibility and organic reach with powerful SEO features and tools.
- **Marketing and Customer Engagement**: Drive customer acquisition, retention, and loyalty through targeted marketing campaigns and promotions.
- **Simplified Checkout Process**: Streamline the checkout process for a frictionless and transparent buying experience.
- **Mobile Commerce**: Optimize the mobile shopping experience with convenient features and seamless communication.


## Installation

1. [Install Bench](https://github.com/frappe/bench#installation).

2. Once bench is installed, add the Go1 Commerce app to your bench by running

    ```sh
    $ bench get-app https://github.com/TridotsTech/Go1-Commerce
    ```

3. Then you have to install the Go1 Commerce app on the required site by running

    ```sh
    $ bench --site sitename install-app go1_commerce
    ```
    
4. Enable the server by running
    
     ```sh
    $ bench set-config -g server_script_enabled 1
    ```
