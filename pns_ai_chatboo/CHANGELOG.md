# Changelog

What changes for people who use this module, one section per published version, newest first. The heading is the git tag.

## owl1-2.1.553_owl2-2.1.553 (2026-11-06)

- The AI-generated mark also goes on PDFs saved as attachments and on HTML exports. Text and Markdown have no properties and stay unmarked.

## owl1-2.1.552_owl2-2.1.552 (2026-11-06)

- The prompt box now reads "Ask Chatboo AI...", so it is plain that an AI answers.
- Answers, and the PDF and Word files exported from them, carry a machine-readable mark that an AI system made them (EU AI Act, article 50). Nothing else changes on screen.

## owl1-2.1.551_owl2-2.1.551 (2026-11-06)

- The `/financial-health` skill description no longer ends with an internal reference code that meant nothing outside the original database.

## owl1-2.1.550_owl2-2.1.550 (2026-11-06)

- The module website now points to the product page at www.patanegra.com. The Apps sheet still shows as the module description inside Odoo.
- README: the language line links to the product page too.

## owl1-2.1.549_owl2-2.1.549 (2026-11-05)

- README: new "What it does not do" and "Questions" sections, in English and Spanish (who can use it, who can confirm changes, where questions go, how the voice works).

## owl1-2.1.548_owl2-2.1.548 (2026-11-05)

- Store page: the EN tab now shows as selected, so the language switch looks like a switch.

## owl1-2.1.547_owl2-2.1.547 (2026-11-05)

- Store page: the Spanish text was hidden for good and the ES tab did nothing. Now both languages show, one after the other, and ES jumps to the Spanish part.
- Apps sheet: the language tabs stay at the top while you scroll.

## owl1-2.1.546_owl2-2.1.546 (2026-11-04)

- The module is now named "Chatboo — AI Chat Assistant", so the store listing says what it is.

## owl1-2.1.545_owl2-2.1.545 (2026-11-04)

- The module moves to the Productivity category in Apps and in the store.
- New one-line summary: "AI chat assistant inside Odoo: ask about your records, with the permissions of whoever asks, and get tables, charts and PDF or Excel answers."
- Store page: the thumbnail no longer cuts off the sides of the headline.

## owl1-2.1.543_owl2-2.1.543 (2026-11-04)

- README: Getting started explains both ways to install: from the Odoo Apps Store, or by cloning the three repositories on the same series. Installing Chatboo brings the AI Engine and PNS Base with it.

## owl1-2.1.542_owl2-2.1.542 (2026-11-03)

- First public release, for Odoo 14.0 and 19.0. An AI chat opens from the top bar over the current screen, knows which record or list is on it, and answers with the permissions of the person who asks.
- Answers come as tables whose cells open the record, and charts. They can be exported to PDF, Excel or Word, or read aloud. You can attach a spreadsheet, a Word file, a PDF, an image or plain text and ask about it.
- Type `/` to run a skill: a procedure written once that most of the time runs without calling the AI. A good answer can be saved as a new skill from the chat.
- Changes are a plan with a Confirm button that only allowed users can press. Conversations are saved per user. Runs on the AI Engine (`pns_ai_mcp`).
