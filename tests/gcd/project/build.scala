import sbt._
import Keys._
  
object BuildSettings
{
  val buildOrganization = "edu.berkeley.cs"
  val buildVersion = "1.1"
  val buildScalaVersion = "2.10.2"

  def apply(projectdir: String) = {
    Defaults.defaultSettings ++ Seq (
      organization := buildOrganization,
      version      := buildVersion,
      scalaVersion := buildScalaVersion,
      scalaSource in Compile := Path.absolute(file(projectdir + "/src")),
      resourceDirectory in Compile := Path.absolute(file(projectdir + "/src")),
//      resolvers += "Sonatype OSS Snapshots" at "https://oss.sonatype.org/content/repositories/snapshots",
//      resolvers += Classpaths.typesafeResolver,
      resolvers += "scct-github-repository" at "http://mtkopone.github.com/scct/maven-repo",
//      addSbtPlugin("reaktor" % "sbt-scct" % "0.2-SNAPSHOT"),
      libraryDependencies += "edu.berkeley.cs" %% "chisel" % "2.0"
    )
  }
}

object ChiselBuild extends Build
{
  import BuildSettings._
  lazy val main = Project("main", file("main"), settings = BuildSettings("."))
}

