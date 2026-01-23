import assert from "node:assert"
import test from "node:test"
import { initiateCall, sendFax, sendSms } from "@/services/comms/telnyx"

test("telnyx service exports", () => {
  assert.equal(typeof sendSms, "function")
  assert.equal(typeof sendFax, "function")
  assert.equal(typeof initiateCall, "function")
})
