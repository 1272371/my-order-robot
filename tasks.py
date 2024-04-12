from robocorp.tasks import task
from robocorp import browser
from RPA.Tables import Tables
from RPA.HTTP import HTTP
from RPA.PDF import PDF
from RPA.Archive import Archive
import shutil

@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    - Opens the robot order website.
    - Retrieves robot orders from a CSV file.
    - Fills the order form for each robot.
    - Stores order receipts as PDF files.
    - Takes screenshots of ordered robots.
    - Embeds screenshots into PDF receipts.
    - Archives receipts and cleanup temporary folders.
    """
    browser.configure(slowmo=100, headless=True)
    open_robot_order_website()
    orders = get_orders(output_file='orders.csv', overwrite=True)
    for order in orders:
        fill_the_form(order)
    archive_receipts()

def open_robot_order_website():
    """
    Opens the Robot Spare Bin Industries website for robot orders.
    """
    url = 'https://robotsparebinindustries.com/#/robot-order'
    browser.goto(url=url)

def get_orders(output_file='orders.csv', overwrite=True):
    """
    Downloads the robot orders CSV file and reads its contents into a table.

    Args:
        output_file (str): Path to save the downloaded CSV file.
        overwrite (bool): Flag to overwrite existing file if it exists.

    Returns:
        list of dict: List of dictionaries representing the robot orders.
    """
    http = HTTP()
    http.download("https://robotsparebinindustries.com/orders.csv", overwrite=overwrite)
    table = Tables()
    return table.read_table_from_csv(output_file)

def close_annoying_modal():
    """
    Closes an annoying modal dialog on the page.
    """
    page = browser.page()
    page.click('#root > div > div.modal > div > div > div > div > div > button.btn.btn-dark')

def fill_the_form(order):
    """
    Fills the robot order form with the specified order details.

    Args:
        order (dict): Dictionary containing order details.
    """
    close_annoying_modal()
    page = browser.page()
    head_names = {
        "1": "Roll-a-thor head",
        "2": "Peanut crusher head",
        "3": "D.A.V.E head",
        "4": "Andy Roid head",
        "5": "Spanner mate head",
        "6": "Drillbit 2000 head"
    }
    head_number = order["Head"]
    page.select_option("#head", head_names.get(head_number))
    page.click(f'//*[@id="root"]/div/div[1]/div/div[1]/form/div[2]/div/div[{order["Body"]}]/label')
    page.fill("input[placeholder='Enter the part number for the legs']", order["Legs"])
    page.fill("#address", order["Address"])
    page.click("#order")

    while not page.query_selector("#order-another"):
        page.click("#order")

    pdf_path = store_receipt_as_pdf(int(order["Order number"]))
    screenshot_path = screenshot_robot(int(order["Order number"]))
    embed_screenshot_to_receipt(screenshot_path, pdf_path)
    clicks()

def clicks():
    """
    Simulates a click action.
    """
    page = browser.page()
    page.click('#order-another')

def store_receipt_as_pdf(order_number):
    """
    Generates a PDF receipt for the specified order number.

    Args:
        order_number (int): Unique order number.

    Returns:
        str or None: File path of the generated PDF receipt or None if an error occurs.
    """
    pdf = PDF()
    pdf_path = f"output/receipts/receipt_{order_number}.pdf"
    try:
        page = browser.page()
        order_receipt_html = page.locator("#receipt").inner_html()
        pdf.html_to_pdf(order_receipt_html, pdf_path)
        return pdf_path
    except Exception as e:
        print(f"Error occurred while creating the PDF receipt: {str(e)}")
        return None

def screenshot_robot(order_number):
    """
    Takes a screenshot of the robot preview image.

    Args:
        order_number (int): Unique order number.

    Returns:
        str: File path of the captured screenshot.
    """
    page = browser.page()
    screenshot_path = f"output/screenshots/{order_number}.png"
    page.locator("#robot-preview-image").screenshot(path=screenshot_path)
    return screenshot_path

def embed_screenshot_to_receipt(screenshot_path, pdf_path):
    """
    Embeds a screenshot into a PDF receipt.

    Args:
        screenshot_path (str): File path of the screenshot.
        pdf_path (str): File path of the PDF receipt.
    """
    try:
        pdf = PDF()
        pdf.add_watermark_image_to_pdf(image_path=screenshot_path, source_path=pdf_path, output_path=pdf_path)
    except Exception as e:
        print(f"Error occurred while embedding screenshot to PDF: {str(e)}")

def archive_receipts():
    """
    Archives receipt PDF files into a ZIP file.
    """
    lib = Archive()
    lib.archive_folder_with_zip("./output/receipts", "./output/receipts.zip")
