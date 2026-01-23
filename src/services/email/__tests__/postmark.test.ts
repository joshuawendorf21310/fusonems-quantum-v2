import assert from "node:assert"
import test from "node:test"
import { sendEmail } from "@/services/email/postmark"

test("postmark service export", () => {
  assert.equal(typeof sendEmail, "function")
})
