package Main

import Chisel._
  
object Main {
  def main(args: Array[String]) = {
    //val boot_args = args ++ Array("--target-dir", "generated-src","--gen-harness");
    val res = chiselMain( args, () => Module ( new GCD() ) )
  } 
}   
