package Main

import Chisel._
import Node._

class GCD_io extends Bundle() {
  val operands_bits_A   = Bits(INPUT, 16)
  val operands_bits_B   = Bits(INPUT, 16)
  val operands_val      = Bool(INPUT)
  val operands_rdy      = Bool(OUTPUT)

  val result_bits_data  = Bits(OUTPUT, 16)
  val result_val        = Bool(OUTPUT)
  val result_rdy        = Bool(INPUT)
}

class GCD extends Module {
  val io = new GCD_io();

  // Your code goes here...
  val load_ext = Bool()
  val next_A = UInt()
  val next_B = UInt()
  
  val latch_A = Reg(next = Mux(load_ext, io.operands_bits_A, next_A))
  val latch_B = Reg(next = Mux(load_ext, io.operands_bits_B, next_B))

  // if b > a, swap (so a >= b)
  val b_gt_a = latch_B > latch_A
  val swapped_A = Mux(b_gt_a, latch_B, latch_A)
  val swapped_B = Mux(b_gt_a, latch_A, latch_B)
  
  // subtract a-b and feed into next A, feed swapped B into next B 
  val a_sub_b = swapped_A - swapped_B
  next_A := a_sub_b
  next_B := swapped_B
  
  io.result_bits_data := a_sub_b
  
  // external interface controller
  val s_idle :: s_calc :: s_done :: Nil = Enum(UInt(), 3)
  val state = Reg(init = s_idle)
  when (state === s_idle) {
    when  (io.operands_val) { state := s_calc }
  }.elsewhen (state === s_calc) {
    when (next_B === UInt(0)) { state := s_done }
  }.elsewhen (state === s_done) {
    when (io.result_rdy) { state := s_idle }
  }
  
  io.operands_rdy := (state === s_idle)
  load_ext := ((state === s_idle) && (io.operands_val))
  io.result_val := (state === s_done)
}

object Main {
  def main(args: Array[String]) = {
    val res = chiselMain( args, () => Module ( new GCD() ) )
  } 
}

