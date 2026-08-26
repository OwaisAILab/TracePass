# TracePass — General Digital Product Passport Platform

TracePass is an industry-independent Digital Product Passport (DPP) and supply-chain traceability platform. Fashion is no longer the product identity; it is only one possible demonstration category.

## Generic model

Industry → Product Category → Product Template → Product → Materials/Components → Supply Chain → Evidence → Compliance → Lifecycle → QR/Public Passport

## Product templates

Administrators can define category-specific fields. A template field is represented as:

`key|Label|type|required|help text`

Supported field types: `text`, `number`, `date`, `textarea`.

The manufacturer's product form automatically renders the selected category's template fields and stores their values as JSON in the product record.

## Starter industries

- Apparel
- Batteries
- Electronics
- Furniture
- Automotive
- Packaging

More industries, categories and templates can be added from the Admin console.

## Existing core preserved

The final general-purpose TracePass release keeps the core workflows: role-based access, organizations, supplier material offerings, procurement and negotiated pricing, product passports, batches, materials, supply-chain events, shipments, certificates/documents, compliance rules/checks/reviews, recalls/incidents, notifications, audit logs, QR/public verification, reporting, REST API and deployment files.

## Demonstration concept

The online marketplace is now a demonstration surface for the DPP platform. Products may belong to any configured industry. The public passport shows the industry, category, template-driven product information, materials, manufacturing batches and compliance status without exposing internal records.
