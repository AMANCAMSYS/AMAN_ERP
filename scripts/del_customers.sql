
\c aman_b08f3451
BEGIN;
DELETE FROM payment_allocations WHERE payment_id IN (SELECT id FROM payment_vouchers WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE));
DELETE FROM payment_vouchers WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE);
DELETE FROM invoice_lines WHERE invoice_id IN (SELECT id FROM invoices WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE));
DELETE FROM invoices WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE);
DELETE FROM sales_order_lines WHERE sales_order_id IN (SELECT id FROM sales_orders WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE));
DELETE FROM sales_orders WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE);
DELETE FROM sales_quotation_lines WHERE quotation_id IN (SELECT id FROM sales_quotations WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE));
DELETE FROM sales_quotations WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE);
DELETE FROM sales_return_lines WHERE return_id IN (SELECT id FROM sales_returns WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE));
DELETE FROM sales_returns WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE);
DELETE FROM parties WHERE is_customer = TRUE;
COMMIT;
