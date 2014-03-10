import sbt._
import Keys._
  
object BuildSettings
{
  val buildOrganization = "edu.berkeley.cs"
  val buildVersion = "1.1"
  val buildScalaVersion = "2.10.1"

  def apply() = {
    Defaults.defaultSettings ++ Seq (
      organization := buildOrganization,
      version      := buildVersion,
      scalaVersion := buildScalaVersion
    )
  }
}

object ChiselBuild extends Build
{
  import BuildSettings._
  //lazy val chisel = RootProject(file("/home/ducky/git/chisel"))

  lazy val main = Project("main", file("."), settings = BuildSettings()).dependsOn(chisel)
  lazy val chisel = Project("chisel", file("chisel"), settings = BuildSettings())

  //lazy val chisel = Project("chisel", file("chisel"), settings = BuildSettings("../../../chisel/src/main/scala"))
  //lazy val chisel = ProjectRef(file("../../../chisel"), "chisel")
//  lazy val chisel = Project("chisel", file("chisel"), settings = BuildSettings("../../../chisel"))
}

